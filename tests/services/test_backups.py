import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.database.connection import get_connection, set_commit_listener, transaction
from app.database.migrations.runner import CURRENT_SCHEMA_VERSION, run_migrations
from app.database.repositories.forms import (
    get_medical_history,
    get_mullen_assessment,
    get_mullen_assessment_context,
    save_medical_history,
    save_mullen_assessment,
    save_procedure_schedule,
)
from app.database.repositories.patients import (
    complete_patient_form,
    create_patient,
    delete_patient,
    get_patient,
    update_patient,
)
from app.database.repositories.videos import create_patient_video, list_patient_videos
from app.database.schema import SCHEMA_SQL
from app.services import backups
from app.services.backups import (
    BackupError,
    BackupManager,
    BackupValidationError,
    inspect_backup,
)


@pytest.fixture
def manager(temp_database, monkeypatch):
    manager = BackupManager(temp_database)
    monkeypatch.setattr(backups, "_manager", manager)
    yield manager
    manager.close()


def test_complete_database_round_trip_preserves_values_and_current_recovery_copy(
    manager,
):
    patient_id = create_patient("BACKUP-1")
    update_patient(
        patient_id, {"child_name": "Original", "date_of_birth": "2025-01-01", "risk": 0}
    )
    save_medical_history(patient_id, {"seen_neurologist": 0, "head_injury": None})
    save_procedure_schedule(patient_id, "Recording", {"room": "Room A"})
    context = {
        "assessment_date": "2025-03-01",
        "scoring_date_of_birth": "2025-01-01",
        "confidence_level": 90,
        "age_calculation": "calendar",
    }
    save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 0, "t_score": 20}}, context=context
    )
    create_patient_video(
        patient_id, {"title": "Recording", "file_path": "D:/videos/example.mp4"}
    )
    complete_patient_form(patient_id, "Original Screener")

    with get_connection() as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"
            )
        ]
        original = {
            name: [
                tuple(row)
                for row in connection.execute(f'SELECT * FROM "{name}" ORDER BY rowid')
            ]
            for name in tables
        }
    backup = manager.create_backup()
    digest = hashlib.sha256(backup.path.read_bytes()).digest()
    update_patient(patient_id, {"child_name": "New name"})
    create_patient("LATER-PATIENT")

    result = manager.restore(backup.path)
    assert result.recovery_path != backup.path
    assert inspect_backup(result.recovery_path).patient_count == 2
    assert hashlib.sha256(backup.path.read_bytes()).digest() == digest
    with get_connection() as connection:
        restored = {
            name: [
                tuple(row)
                for row in connection.execute(f'SELECT * FROM "{name}" ORDER BY rowid')
            ]
            for name in tables
        }
    assert restored == original
    assert get_patient(patient_id)["form_status"] == "Complete"
    assert get_medical_history(patient_id)["seen_neurologist"] == 0
    assert get_medical_history(patient_id)["head_injury"] is None
    assert get_mullen_assessment(patient_id)["gross_motor"]["raw_score"] == 0
    assert get_mullen_assessment_context(patient_id) == context
    assert list_patient_videos(patient_id)[0]["file_path"] == "D:/videos/example.mp4"


def test_each_manual_backup_is_a_new_file_and_prior_state_stays_available(manager):
    patient_id = create_patient("HISTORY")
    first = manager.create_backup()
    delete_patient(patient_id)
    second = manager.create_backup()
    assert first.path != second.path
    assert inspect_backup(first.path).patient_count == 1
    assert inspect_backup(second.path).patient_count == 0


@pytest.mark.parametrize(
    "invalid",
    [
        "not-sqlite",
        "other-database",
        "newer",
        "missing-table",
        "broken-relationship",
        "trigger",
    ],
)
def test_invalid_restore_preserves_live_database(manager, tmp_path, invalid):
    patient_id = create_patient("KEEP")
    if invalid == "not-sqlite":
        candidate = tmp_path / "invalid.db"
        candidate.write_bytes(b"This is not a database")
    elif invalid == "other-database":
        candidate = tmp_path / "other.db"
        with closing(sqlite3.connect(candidate)) as connection:
            connection.execute("CREATE TABLE unrelated (id INTEGER)")
    else:
        candidate = manager.create_backup().path
        with closing(sqlite3.connect(candidate)) as connection:
            if invalid == "newer":
                connection.execute(
                    f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION + 1}"
                )
            elif invalid == "missing-table":
                connection.execute("DROP TABLE medical_histories")
            elif invalid == "broken-relationship":
                connection.execute(
                    "INSERT INTO medical_histories(patient_id) VALUES (999)"
                )
            else:
                connection.execute(
                    "CREATE TRIGGER unexpected AFTER DELETE ON patients BEGIN DELETE FROM medical_histories; END"
                )
            connection.commit()
    before = manager.database.read_bytes()
    with pytest.raises(BackupValidationError):
        manager.restore(candidate)
    assert manager.database.read_bytes() == before
    assert get_patient(patient_id)["subject_id"] == "KEEP"


def test_backup_failure_keeps_older_copy_and_cleans_temporary_files(
    manager, monkeypatch
):
    create_patient("KEEP-BACKUP")
    original = manager.create_backup()
    contents = original.path.read_bytes()

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr(backups, "_copy_database", fail)
    with pytest.raises(BackupError, match="disk full"):
        manager.create_backup()
    assert original.path.read_bytes() == contents
    assert not list(original.path.parent.glob("*.partial"))


def test_restore_write_failure_preserves_current_database_and_source(
    manager, monkeypatch
):
    patient_id = create_patient("RESTORE-FAILURE")
    source = manager.create_backup()
    update_patient(patient_id, {"child_name": "Keep current name"})
    copy = backups._copy_database

    def fail_live(source, destination):
        if destination == manager.database:
            raise OSError("destination unavailable")
        copy(source, destination)

    monkeypatch.setattr(backups, "_copy_database", fail_live)
    with pytest.raises(BackupError, match="destination unavailable"):
        manager.restore(source.path)
    assert get_patient(patient_id)["child_name"] == "Keep current name"
    assert inspect_backup(source.path).patient_count == 1
    assert not list(manager.database.parent.glob("*.partial"))


def test_older_backup_is_migrated_in_staging_without_modifying_source(
    manager, tmp_path
):
    source = tmp_path / "legacy.db"
    legacy_schema = SCHEMA_SQL
    for column in (
        "assessment_date TEXT",
        "scoring_date_of_birth TEXT",
        "confidence_level INTEGER",
        "age_calculation TEXT",
    ):
        legacy_schema = legacy_schema.replace(f"    {column},\n", "")
    with closing(sqlite3.connect(source)) as connection:
        connection.executescript(legacy_schema)
        connection.execute("PRAGMA user_version = 7")
        connection.execute("INSERT INTO patients(subject_id) VALUES ('LEGACY')")
        connection.commit()
    original = source.read_bytes()
    result = manager.restore(source)
    assert result.restored.schema_version == CURRENT_SCHEMA_VERSION
    assert get_patient(1)["subject_id"] == "LEGACY"
    assert source.read_bytes() == original
    assert inspect_backup(manager.database).schema_version == CURRENT_SCHEMA_VERSION


def test_corrupt_database_is_archived_and_recovered(manager):
    create_patient("RECOVER-ME")
    source = manager.create_backup()
    damaged = b"damaged database bytes"
    manager.database.write_bytes(damaged)
    result = manager.restore(source.path)
    assert result.recovery_path.suffix == ".zip"
    with ZipFile(result.recovery_path) as archive:
        assert archive.read(manager.database.name) == damaged
    assert get_patient(1)["subject_id"] == "RECOVER-ME"


def test_restore_missing_database_and_reject_active_file(manager):
    create_patient("MISSING")
    source = manager.create_backup()
    manager.database.unlink()
    assert manager.restore(source.path).recovery_path is None
    assert get_patient(1)["subject_id"] == "MISSING"
    with pytest.raises(BackupError, match="active database"):
        manager.restore(manager.database)


def test_automatic_backup_failure_does_not_fail_committed_save(manager, monkeypatch):
    manager.start()
    previous = manager.last_backup

    def fail(**kwargs):
        raise BackupError("backup disk is unavailable")

    monkeypatch.setattr(manager, "create_backup", fail)
    patient_id = create_patient("SAVED-WITHOUT-BACKUP")
    manager.close()
    assert get_patient(patient_id)["subject_id"] == "SAVED-WITHOUT-BACKUP"
    assert "backup disk is unavailable" in manager.last_error
    assert previous.exists()


def test_one_notification_per_commit_and_none_for_reads_or_rollbacks(manager):
    patient_id = create_patient("COMMIT-HOOK")
    calls = []
    set_commit_listener(lambda: calls.append("committed"))
    get_patient(patient_id)
    with transaction() as connection:
        update_patient(patient_id, {"child_name": "Discard"})
        connection.rollback()
    assert calls == []
    with transaction():
        update_patient(patient_id, {"child_name": "Keep"})
        complete_patient_form(patient_id, "Staff")
    assert calls == ["committed"]


def test_delete_preserves_snapshot_before_cascading_rows(manager):
    patient_id = create_patient("DELETE")
    save_medical_history(patient_id, {"general_health": "Original history"})
    manager.start()
    delete_patient(patient_id)
    manager.close()
    snapshots = list(backups.backup_directory().glob("edc-before-delete-*.sqlite3"))
    assert len(snapshots) == 1
    assert inspect_backup(snapshots[0]).patient_count == 1
    assert get_patient(patient_id) is None
    manager.restore(snapshots[0])
    assert get_medical_history(patient_id)["general_health"] == "Original history"


def test_failed_protective_backup_blocks_deletion(manager, monkeypatch):
    patient_id = create_patient("DO-NOT-DELETE")
    manager.start()

    def fail(**kwargs):
        raise BackupError("cannot preserve previous state")

    monkeypatch.setattr(manager, "create_backup", fail)
    with pytest.raises(BackupError, match="cannot preserve"):
        delete_patient(patient_id)
    assert get_patient(patient_id) is not None


def test_upgrade_preserves_original_version_before_migration(manager):
    create_patient("UPGRADE")
    with get_connection() as connection:
        connection.execute("PRAGMA user_version = 7")
    run_migrations()
    files = list(backups.backup_directory().glob("edc-before-upgrade-*.sqlite3"))
    assert len(files) == 1
    assert inspect_backup(files[0]).schema_version == 7
    assert inspect_backup(manager.database).schema_version == CURRENT_SCHEMA_VERSION


def test_invalid_database_requires_recovery_before_migration(manager):
    with get_connection() as connection:
        connection.execute("DROP TABLE medical_histories")
        connection.execute("PRAGMA user_version = 7")
    before = manager.database.read_bytes()
    with pytest.raises(BackupValidationError):
        run_migrations()
    assert manager.database.read_bytes() == before


def test_retention_keeps_daily_history_and_never_removes_manual_or_recovery(
    manager, monkeypatch
):
    directory = backups.backup_directory()
    directory.mkdir()
    monkeypatch.setattr(backups, "AUTOMATIC_RECENT", 2)
    monkeypatch.setattr(backups, "AUTOMATIC_DAYS", 2)
    names = [
        f"edc-auto-202610{day:02}T{hour:02}0000000000Z-12345678.sqlite3"
        for day in (19, 20, 21)
        for hour in (9, 10)
    ]
    for name in [*names, "edc-manual-old.sqlite3", "edc-before-restore-old.sqlite3"]:
        (directory / name).write_bytes(b"snapshot")
    manager._prune_automatic(directory)
    remaining = {path.name for path in directory.iterdir()}
    assert remaining == {
        names[-1],
        names[-2],
        names[3],
        "edc-manual-old.sqlite3",
        "edc-before-restore-old.sqlite3",
    }


def test_wal_database_backup_and_restore_includes_committed_changes(manager):
    with closing(sqlite3.connect(manager.database)) as keeper:
        assert keeper.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        keeper.execute("INSERT INTO patients(subject_id) VALUES ('WAL-PATIENT')")
        keeper.commit()
        assert Path(str(manager.database) + "-wal").exists()
        backup = manager.create_backup()
        assert backup.patient_count == 1
        keeper.execute("UPDATE patients SET child_name = 'Later WAL change'")
        keeper.commit()
        manager.restore(backup.path)
        assert keeper.execute("SELECT child_name FROM patients").fetchone()[0] is None
        assert get_patient(1)["subject_id"] == "WAL-PATIENT"


def test_interrupted_sqlite_restore_really_rolls_back_destination(
    manager, monkeypatch, tmp_path
):
    source = tmp_path / "large-source.db"
    create_patient("KEEP-DESTINATION")
    initial = manager.create_backup().path
    backups._copy_database(initial, source)
    with closing(sqlite3.connect(source)) as connection:
        connection.execute(
            "UPDATE patients SET child_name = 'Must not reach destination'"
        )
        connection.execute(
            "INSERT INTO export_logs(output_path) VALUES (?)", ("x" * 3_000_000,)
        )
        connection.commit()
    # Expire during a multi-step backup after pages have already been written.
    ticks = iter((0, 100))
    monkeypatch.setattr(backups.time, "monotonic", lambda: next(ticks, 100))
    with pytest.raises(BackupError, match="too long"):
        backups._copy_database(source, manager.database)
    assert get_patient(1)["child_name"] is None
    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM export_logs").fetchone()[0] == 0


def test_failed_recovery_copy_blocks_restore(manager, monkeypatch):
    patient_id = create_patient("KEEP-WHEN-BACKUP-FAILS")
    source = manager.create_backup().path
    update_patient(patient_id, {"child_name": "Current state"})

    def fail(**kwargs):
        raise BackupError("recovery storage unavailable")

    monkeypatch.setattr(manager, "create_backup", fail)
    with pytest.raises(BackupError, match="recovery storage unavailable"):
        manager.restore(source)
    assert get_patient(patient_id)["child_name"] == "Current state"
