import sqlite3
from contextlib import closing

from app import config
from app.database.connection import get_connection
from app.database.migrations.versions import (
    v001_initial,
    v002_add_form_status,
    v003_patient_videos,
    v004_mullen,
    v005_screening_comments,
    v006_patient_risk,
    v007_shared_patient_fields,
    v008_mullen_scoring_context,
)

MIGRATIONS = (
    v001_initial,
    v002_add_form_status,
    v003_patient_videos,
    v004_mullen,
    v005_screening_comments,
    v006_patient_risk,
    v007_shared_patient_fields,
    v008_mullen_scoring_context,
)

CURRENT_SCHEMA_VERSION = MIGRATIONS[-1].VERSION


class MigrationBackupError(RuntimeError):
    pass


def get_schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")


def migrate_connection(connection: sqlite3.Connection) -> None:
    """Upgrade a live database or an isolated restore candidate."""
    current_version = get_schema_version(connection)
    if current_version > CURRENT_SCHEMA_VERSION:
        raise ValueError("This database needs a newer version of the application.")

    for migration in MIGRATIONS:
        if migration.VERSION <= current_version:
            continue

        migration.upgrade(connection)
        set_schema_version(connection, migration.VERSION)
        current_version = migration.VERSION


def run_migrations() -> None:
    if config.DATABASE_PATH.exists() and config.DATABASE_PATH.stat().st_size:
        with closing(sqlite3.connect(config.DATABASE_PATH)) as connection:
            version = get_schema_version(connection)
            populated = connection.execute(
                "SELECT 1 FROM sqlite_schema WHERE name = 'patients'"
            ).fetchone()
        if populated and version < CURRENT_SCHEMA_VERSION:
            from app.services.backups import (
                BackupError,
                BackupValidationError,
                get_backup_manager,
            )

            try:
                get_backup_manager().create_backup(kind="before-upgrade")
            except BackupValidationError:
                # An invalid database needs recovery, not a different backup folder.
                raise
            except BackupError as exc:
                raise MigrationBackupError(
                    f"The database upgrade was paused because its recovery copy could not be created: {exc}"
                ) from exc
    with get_connection() as connection:
        migrate_connection(connection)
