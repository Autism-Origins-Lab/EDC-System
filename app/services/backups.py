"""Validated SQLite snapshots and recovery, independent of application connections."""

import logging
import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from app import config
from app.database.connection import database_maintenance, set_commit_listener
from app.services.preferences import load_preferences

AUTOMATIC_RECENT = 20
AUTOMATIC_DAYS = 30
COPY_TIMEOUT = 10


class BackupError(RuntimeError):
    pass


class BackupValidationError(BackupError):
    pass


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: datetime
    patient_count: int
    schema_version: int


@dataclass(frozen=True)
class RestoreResult:
    restored: BackupInfo
    recovery_path: Path | None


def backup_directory() -> Path:
    configured = load_preferences().get("backup_directory", "")
    return Path(configured) if configured else config.DATABASE_PATH.parent / "backups"


def _open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA trusted_schema = OFF")
        connection.execute("PRAGMA query_only = ON")
    except BaseException:
        connection.close()
        raise
    return connection


def _validate(
    connection: sqlite3.Connection, *, current: bool = False
) -> tuple[int, int]:
    from app.database.migrations.runner import CURRENT_SCHEMA_VERSION
    from app.database.schema import SCHEMA_SQL

    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if not 0 <= version <= CURRENT_SCHEMA_VERSION:
        raise BackupValidationError(
            "This backup needs a newer version of the application."
        )
    if current and version != CURRENT_SCHEMA_VERSION:
        raise BackupValidationError("Database upgrade did not complete.")
    if [tuple(row) for row in connection.execute("PRAGMA integrity_check")] != [
        ("ok",)
    ]:
        raise BackupValidationError("The database failed its integrity check.")
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise BackupValidationError(
            "The database contains broken patient/form relationships."
        )
    if connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type IN ('trigger', 'view') LIMIT 1"
    ).fetchone():
        raise BackupValidationError(
            "Unexpected database triggers or views in this file."
        )

    required = {
        "patients",
        "telephone_screenings",
        "screening_questionnaires",
        "medical_histories",
        "family_medical_histories",
        "procedure_schedules",
        "export_logs",
    }
    actual = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table'"
        )
    }
    if not required <= actual:
        raise BackupValidationError("This file is not a supported EDC database.")
    if current or version == CURRENT_SCHEMA_VERSION:
        with closing(sqlite3.connect(":memory:")) as expected:
            expected.executescript(SCHEMA_SQL)
            tables = expected.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            for (table,) in tables:
                if table not in actual:
                    raise BackupValidationError(f"Missing database table: {table}.")
                columns = {
                    row[1]
                    for row in connection.execute(f'PRAGMA table_info("{table}")')
                }
                wanted = {
                    row[1] for row in expected.execute(f'PRAGMA table_info("{table}")')
                }
                if not wanted <= columns:
                    raise BackupValidationError(f"Missing columns in {table}.")

                def keys(conn, table=table):
                    return {
                        (row[3], row[2], row[4], row[6])
                        for row in conn.execute(f'PRAGMA foreign_key_list("{table}")')
                    }

                if keys(connection) != keys(expected):
                    raise BackupValidationError(f"Unexpected relationships in {table}.")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(patients)")}
    if not {"id", "subject_id"} <= columns:
        raise BackupValidationError("This file is not a supported EDC database.")
    return version, connection.execute("SELECT COUNT(*) FROM patients").fetchone()[0]


def inspect_backup(path: Path) -> BackupInfo:
    path = Path(path).resolve()
    try:
        with closing(_open_readonly(path)) as connection:
            version, count = _validate(connection)
        return BackupInfo(
            path, datetime.fromtimestamp(path.stat().st_mtime, UTC), count, version
        )
    except sqlite3.Error as exc:
        raise BackupValidationError(f"Unable to read this database: {exc}") from exc
    except OSError as exc:
        raise BackupError(str(exc)) from exc


def _copy_database(source: Path, destination: Path) -> None:
    deadline = time.monotonic() + COPY_TIMEOUT

    def progress(status, remaining, total):
        if status != sqlite3.SQLITE_DONE and time.monotonic() > deadline:
            raise BackupError(
                "Database is busy or copying took too long. Please try again."
            )

    with (
        closing(_open_readonly(source)) as reader,
        closing(sqlite3.connect(destination)) as writer,
    ):
        reader.backup(writer, pages=128, progress=progress, sleep=0.05)


def _temporary_path(directory: Path) -> Path:
    with NamedTemporaryFile(
        dir=directory, prefix=".edc-backup-", suffix=".partial", delete=False
    ) as file:
        return Path(file.name)


def _sync(path: Path) -> None:
    # Windows FlushFileBuffers requires a writable handle.
    with path.open("r+b") as file:
        os.fsync(file.fileno())


def _remove_temporary(path: Path | None) -> None:
    if path is not None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logging.getLogger(__name__).warning(
                "Unable to remove temporary backup file", exc_info=True
            )


class BackupManager:
    def __init__(self, database: Path):
        self.database = Path(database).resolve()
        self.last_backup: Path | None = None
        self.last_error: str | None = None
        self._executor: ThreadPoolExecutor | None = None
        self._state_lock = Lock()
        self._pending = False
        self._running = False

    def create_backup(
        self, directory: Path | None = None, *, kind: str = "manual"
    ) -> BackupInfo:
        if kind not in {
            "manual",
            "auto",
            "before-delete",
            "before-upgrade",
            "before-restore",
        }:
            raise ValueError("Unknown backup type.")
        directory = Path(directory or backup_directory()).resolve()
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        output = directory / f"edc-{kind}-{stamp}-{uuid4().hex[:8]}.sqlite3"
        temporary = None
        try:
            with database_maintenance():
                directory.mkdir(parents=True, exist_ok=True)
                temporary = _temporary_path(directory)
                _copy_database(self.database, temporary)
                info = inspect_backup(temporary)
                _sync(temporary)
                temporary.replace(output)
            self.last_backup = output
            self.last_error = None
            return BackupInfo(
                output, info.created_at, info.patient_count, info.schema_version
            )
        except sqlite3.Error as exc:
            raise BackupValidationError(
                f"Database could not be backed up: {exc}"
            ) from exc
        except OSError as exc:
            raise BackupError(f"Backup could not be created: {exc}") from exc
        finally:
            _remove_temporary(temporary)

    def start(self) -> None:
        if self._executor is not None:
            return
        try:
            self.create_backup(kind="auto")
            self._prune_automatic(backup_directory())
        except (BackupError, OSError) as exc:
            self.last_error = str(exc)
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="edc-backup"
        )
        set_commit_listener(self.after_commit)

    def after_commit(self) -> None:
        with self._state_lock:
            self._pending = True
            if self._running or self._executor is None:
                return
            self._running = True
            self._executor.submit(self._automatic_worker)

    def _automatic_worker(self) -> None:
        while True:
            with self._state_lock:
                if not self._pending:
                    self._running = False
                    return
                self._pending = False
            try:
                info = self.create_backup(kind="auto")
                self._prune_automatic(info.path.parent)
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Automatic database backup failed"
                )
                self.last_error = str(exc)

    def _prune_automatic(self, directory: Path) -> None:
        files = sorted(directory.glob("edc-auto-*.sqlite3"), reverse=True)
        keep = set(files[:AUTOMATIC_RECENT])
        days = set()
        for path in files:
            day = path.name.removeprefix("edc-auto-")[:8]
            if day not in days and len(days) < AUTOMATIC_DAYS:
                keep.add(path)
                days.add(day)
        for path in files:
            if path not in keep:
                path.unlink()

    def close(self) -> None:
        set_commit_listener(None)
        executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=True)

    def restore(self, path: Path) -> RestoreResult:
        from app.database.migrations.runner import migrate_connection

        source = Path(path).resolve()
        if source == self.database or (
            self.database.exists()
            and source.exists()
            and source.samefile(self.database)
        ):
            raise BackupError("Select a backup file, not the active database.")
        temporary = None
        try:
            with database_maintenance():
                inspect_backup(source)
                self.database.parent.mkdir(parents=True, exist_ok=True)
                temporary = _temporary_path(self.database.parent)
                _copy_database(source, temporary)
                with closing(sqlite3.connect(temporary)) as staged:
                    staged.row_factory = sqlite3.Row
                    staged.execute("PRAGMA foreign_keys = ON")
                    migrate_connection(staged)
                    staged.commit()
                    _validate(staged, current=True)
                info = inspect_backup(temporary)
                _sync(temporary)
                recovery = None
                damaged = False
                if self.database.exists():
                    try:
                        recovery = self.create_backup(kind="before-restore").path
                    except BackupValidationError:
                        recovery = self._archive_damaged_database()
                        damaged = True
                if not self.database.exists():
                    temporary.replace(self.database)
                elif damaged:
                    self._replace_damaged_database(temporary, recovery)
                else:
                    # SQLite owns the destination write transaction; an interrupted
                    # backup operation rolls it back, including in WAL mode.
                    _copy_database(temporary, self.database)
            self.last_error = None
            return RestoreResult(
                BackupInfo(
                    source, info.created_at, info.patient_count, info.schema_version
                ),
                recovery,
            )
        except sqlite3.Error as exc:
            raise BackupError(f"Unable to restore the database: {exc}") from exc
        except OSError as exc:
            raise BackupError(f"Unable to restore the database: {exc}") from exc
        finally:
            _remove_temporary(temporary)

    def _archive_damaged_database(self) -> Path:
        directory = backup_directory().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        output = (
            directory
            / f"edc-damaged-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}-{uuid4().hex[:8]}.zip"
        )
        temporary = _temporary_path(directory)
        try:
            with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
                for suffix in ("", "-wal", "-shm", "-journal"):
                    file = Path(str(self.database) + suffix)
                    if file.exists():
                        archive.write(file, file.name)
            _sync(temporary)
            temporary.replace(output)
            return output
        finally:
            _remove_temporary(temporary)

    def _replace_damaged_database(self, staged: Path, archive: Path) -> None:
        # A damaged file may not accept SQLite's backup API. Preserve its bytes
        # first, move stale journals aside, then atomically publish the staged file.
        moved = []
        try:
            for suffix in ("-wal", "-shm", "-journal"):
                file = Path(str(self.database) + suffix)
                if file.exists():
                    destination = archive.with_name(archive.name + suffix)
                    file.replace(destination)
                    moved.append((file, destination))
            staged.replace(self.database)
        except BaseException:
            for original, saved in reversed(moved):
                saved.replace(original)
            raise


_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    global _manager
    if _manager is None or _manager.database != config.DATABASE_PATH.resolve():
        _manager = BackupManager(config.DATABASE_PATH)
    return _manager


def backup_before_change(kind: str) -> None:
    manager = get_backup_manager()
    # Automatic protection is enabled by application startup, never by imports.
    if manager._executor is not None:
        manager.create_backup(kind=kind)
