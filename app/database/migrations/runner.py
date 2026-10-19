import sqlite3

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


def get_schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")


def run_migrations() -> None:
    with get_connection() as connection:
        current_version = get_schema_version(connection)

        for migration in MIGRATIONS:
            if migration.VERSION <= current_version:
                continue

            migration.upgrade(connection)
            set_schema_version(connection, migration.VERSION)
            current_version = migration.VERSION
