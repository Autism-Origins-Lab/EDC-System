import sqlite3

import pytest

from app import config
from app.database.connection import get_connection
from app.database.migrations.runner import CURRENT_SCHEMA_VERSION, run_migrations
from app.database.repositories.forms import (
    get_screening_questionnaire,
    save_screening_questionnaire,
)
from app.database.repositories.patients import create_patient, get_patient, update_patient
from app.database.schema import SCHEMA_SQL


def test_questionnaire_identity_failure_rolls_back_both_records(temp_database):
    patient_id = create_patient("ATOMIC")
    save_screening_questionnaire(patient_id, {"child_name": "Original"})
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_identity BEFORE UPDATE OF child_name ON patients "
            "BEGIN SELECT RAISE(ABORT, 'identity failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="identity failure"):
        save_screening_questionnaire(
            patient_id, {"child_name": "Changed", "parent_name": "New"}
        )
    assert get_patient(patient_id)["child_name"] == "Original"
    with get_connection() as connection:
        form = connection.execute(
            "SELECT * FROM screening_questionnaires WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()
    assert form["child_name"] == "Original"
    assert form["parent_name"] is None


def test_overview_risk_failure_rolls_back_identity(temp_database):
    patient_id = create_patient("RISK-ATOMIC")
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_screening BEFORE INSERT ON telephone_screenings "
            "BEGIN SELECT RAISE(ABORT, 'screening failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="screening failure"):
        update_patient(patient_id, {"child_name": "Changed", "risk": 1})
    assert get_patient(patient_id)["child_name"] is None
    assert get_patient(patient_id)["risk"] is None


def test_version_six_migration_preserves_legacy_identity_and_risk(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "legacy.db")
    old_schema = SCHEMA_SQL.replace("    high_familial_risk INTEGER,\n", "").replace(
        "    low_familial_risk INTEGER,\n",
        "",
    )
    with get_connection() as connection:
        connection.executescript(old_schema)
        connection.execute("PRAGMA user_version = 6")
        connection.execute(
            "INSERT INTO patients (subject_id, child_name) VALUES ('OLD', 'Patient Name')"
        )
        connection.execute(
            "INSERT INTO screening_questionnaires (patient_id, child_name, date_of_birth) "
            "VALUES (1, 'Outdated Name', '2026-09-01')"
        )
        connection.execute(
            "INSERT INTO telephone_screenings (patient_id, atRisk) VALUES (1, 0)"
        )
    run_migrations()
    patient = get_patient(1)
    assert patient["child_name"] == "Patient Name"
    assert patient["date_of_birth"] == "2026-09-01"
    assert patient["risk"] == 0
    assert get_screening_questionnaire(1)["child_name"] == "Patient Name"
    with get_connection() as connection:
        screening = connection.execute("SELECT * FROM telephone_screenings").fetchone()
        assert screening["high_familial_risk"] == 0
        assert screening["low_familial_risk"] == 1
        assert (
            connection.execute("PRAGMA user_version").fetchone()[0]
            == CURRENT_SCHEMA_VERSION
        )
    run_migrations()
    assert get_patient(1) == patient
