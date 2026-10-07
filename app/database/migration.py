import sqlite3

from app.database.connection import get_connection
from app.database.schema import SCHEMA_SQL

# updated schema 1 --> 2 (Now includes a patients video table)
# videos have their own unique id but are also related to their individal patient

CURRENT_SCHEMA_VERSION = 8

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

MULLEN_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mullen_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    observations TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mullen_scores(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mullen_assessments_id INTEGER NOT NULL,

  domain TEXT NOT NULL,
  raw_score INTEGER,
  t_score INTEGER,
  band_of_error DECIMAL(5,2),
  percentile_rank INTEGER,
  descriptive_category INTEGER,
  age_equivalence INTEGER,

FOREIGN KEY (mullen_assessments_id) REFERENCES mullen_assessments(id) ON DELETE CASCADE
);
"""

SIBLINGS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS siblings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    name TEXT,
    age TEXT,
    same_bio_father INTEGER,
    same_bio_mother INTEGER,
    adopted INTEGER,
    diagnosis TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
"""

# "Check if:" boxes under family history questions 4 (autism) and 5 (ADHD)
SIBLING_TYPE_COLUMNS = [
    f"sibling_{condition}_{kind}"
    for condition in ("autism", "adhd")
    for kind in ("full", "half", "adopted", "multiple")
]

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

# New Mullen Table added to the current database --> version 3
def migrate_mullen_assessments(connection: sqlite3.Connection) -> None:
    connection.executescript(MULLEN_SCHEMA_SQL)

# A brand-new database already gets form_status from SCHEMA_SQL,
# so only add it to older databases that are missing it.
def migrate_patient_form_status(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(patients)").fetchall()
    columns = {row["name"] for row in table_info}

    if "form_status" not in columns:
        connection.execute("ALTER TABLE patients ADD COLUMN form_status TEXT DEFAULT 'Pending'")

def migrate_patient_risk(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(patients)").fetchall()
    columns = {row["name"] for row in table_info}

    if "risk" not in columns:
        connection.execute("ALTER TABLE patients ADD COLUMN risk BOOLEAN")


def migrate_telephone_screening_comments(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(telephone_screenings)").fetchall()
    columns = {row["name"] for row in table_info}

    if "eligibility_comment" not in columns:
        connection.execute("ALTER TABLE telephone_screenings ADD COLUMN eligibility_comment TEXT")


# Version 7: some databases were created while schema.py had a single atRisk
# column, so add the two columns the telephone screening form saves to.
# atRisk is left in place (unused) on databases that have it.
def migrate_telephone_screening_risk_columns(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(telephone_screenings)").fetchall()
    columns = {row["name"] for row in table_info}

    if "high_familial_risk" not in columns:
        connection.execute("ALTER TABLE telephone_screenings ADD COLUMN high_familial_risk INTEGER")
    if "low_familial_risk" not in columns:
        connection.execute("ALTER TABLE telephone_screenings ADD COLUMN low_familial_risk INTEGER")


# Version 8: the Yes/No family history form adds the sibling "Check if:"
# columns and a siblings table (one row per sibling). This is its own version
# because some databases had already run version 7 before this was written.
# A version number must never change once any database has run it.
def migrate_family_history_siblings(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(family_medical_histories)").fetchall()
    columns = {row["name"] for row in table_info}

    for column in SIBLING_TYPE_COLUMNS:
        if column not in columns:
            connection.execute(
                f"ALTER TABLE family_medical_histories ADD COLUMN {column} INTEGER"
            )

    connection.executescript(SIBLINGS_SCHEMA_SQL)


def run_migrations() -> None:
    with get_connection() as connection:
        version = get_schema_version(connection)

        if version < 1:
            connection.executescript(SCHEMA_SQL)
            set_schema_version(connection, 1)
            version = 1

        if version < 2:
            migrate_patient_form_status(connection)
            set_schema_version(connection, 2)
            version = 2

        if version < 3:
            migrate_patients_video_table(connection)
            set_schema_version(connection, 3)
            version = 3

        if version < 4:
            migrate_mullen_assessments(connection)
            set_schema_version(connection, 4)
            version = 4

        if version < 5:
            migrate_telephone_screening_comments(connection)
            set_schema_version(connection, 5)
            version = 5

        if version < 6:
            migrate_patient_risk(connection)
            set_schema_version(connection,6)
            version = 6

        if version < 7:
            migrate_telephone_screening_risk_columns(connection)
            set_schema_version(connection, 7)
            version = 7

        if version < 8:
            migrate_family_history_siblings(connection)
            set_schema_version(connection, 8)
            version = 8