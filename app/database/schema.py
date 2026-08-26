from app.database.connection import get_connection

SCHEMA_SQL= """

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT NOT NULL UNIQUE,
    child_name TEXT,
    date_of_birth TEXT,
    sex TEXT,
    race TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telephone_screenings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL UNIQUE,
    screening_date TEXT,
    appointment_date TEXT,
    screener TEXT,
    eligibility TEXT,
    high_familial_risk INTEGER,
    low_familial_risk INTEGER,
    schedule_date TEXT,
    birthweight TEXT,
    gestational TEXT,
    verbal_consent INTEGER,
    consent_initials TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS screening_questionnaires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL UNIQUE,
    parent_name TEXT,
    child_name TEXT,
    date_of_birth TEXT,
    age TEXT,
    sex TEXT,
    race TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    home_phone TEXT,
    work_phone TEXT,
    best_time_to_call TEXT,
    fax TEXT,
    email TEXT,
    mother_name TEXT,
    father_name TEXT,
    mother_age TEXT,
    father_age TEXT,
    biological_mother INTEGER,
    biological_mother_name TEXT,
    biological_father INTEGER,
    biological_father_name TEXT,
    research_participation INTEGER,
    research_study TEXT,
    research_study_when TEXT,
    research_study_where TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medical_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL UNIQUE,
    general_health TEXT,
    seen_neurologist INTEGER,
    neurologist_description TEXT,
    head_injury INTEGER,
    head_injury_description TEXT,
    genetic_abnormalities INTEGER,
    genetic_abnormalities_description TEXT,
    seizure_epileptic_attack INTEGER,
    gestational_age TEXT,
    birthweight TEXT,
    birthlength TEXT,
    pregnancy_complications INTEGER,
    pregnancy_complications_description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS family_medical_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL UNIQUE,
    family_psychiatric INTEGER,
    family_psychiatric_description TEXT,
    parent_autism INTEGER,
    parent_schizophrenia INTEGER,
    parent_learning_disability INTEGER,
    parent_substance_abuse INTEGER,
    has_siblings INTEGER,
    sibling_autism INTEGER,
    sibling_adhd INTEGER,
    same_father_as_older_sibling INTEGER,
    same_mother_as_older_sibling INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS procedure_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    procedure_name TEXT NOT NULL,
    procedure_time TEXT,
    research_assistant TEXT,
    room TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_id, procedure_name),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    output_path TEXT NOT NULL,
    exported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)