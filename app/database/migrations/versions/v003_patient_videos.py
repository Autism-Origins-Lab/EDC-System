import sqlite3

VERSION = 3
NAME = "add patient videos"

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


def upgrade(connection: sqlite3.Connection) -> None:
    """Create the video table or migrate its legacy patient association."""
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
