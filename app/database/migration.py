import sqlite3

from app.database.connection import get_connection
from app.database.schema import SCHEMA_SQL

# updated schema 1 --> 2 (Now includes a patients video table)
# videos have their own unique id but are also related to their individal patient

CURRENT_SCHEMA_VERSION = 2

PATIENTS_VIDEO_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS patients_video (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    title TEXT,
    file_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
"""

def get_schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])

def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")
"""
Handles the following:
1. No patients_video table exists yet --> It creates the correct table.
2. patients_video already exists and already has patient_id --> It does nothing, because the table is already correct.
3. if patients_video exists but has no patient_id --> creates a new table and associated
"""

def migrate_patients_video_table(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(patients_video)").fetchall()
    columns = {row["name"] for row in table_info}

    if not table_info:
        connection.executescript(PATIENTS_VIDEO_SCHEMA_SQL)
        return

    if "patient_id" in columns:
        return

    connection.execute("ALTER TABLE patients_video RENAME TO patients_video_legacy")
    connection.executescript(PATIENTS_VIDEO_SCHEMA_SQL)
    connection.execute(
        """
        INSERT INTO patients_video (id, patient_id, title, file_path, created_at, updated_at)
        SELECT
            pv.id,
            pv.id,
            pv.title,
            pv.file_path,
            pv.created_at,
            pv.updated_at
        FROM patients_video_legacy pv
        WHERE EXISTS (
            SELECT 1 FROM patients p WHERE p.id = pv.id
        )
        """
    )


def run_migrations() -> None:
    with get_connection() as connection:
        version = get_schema_version(connection)

        if version < 1:
            connection.executescript(SCHEMA_SQL)
            set_schema_version(connection, 1)
            version = 1

        if version < 2:
            migrate_patients_video_table(connection)
            set_schema_version(connection, CURRENT_SCHEMA_VERSION)
