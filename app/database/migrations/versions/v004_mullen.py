import sqlite3

VERSION = 4
NAME = "add Mullen assessments"

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


def upgrade(connection: sqlite3.Connection) -> None:
    connection.executescript(MULLEN_SCHEMA_SQL)
