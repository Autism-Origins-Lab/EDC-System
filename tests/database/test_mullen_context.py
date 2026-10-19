import sqlite3

import pytest

from app import config
from app.database.connection import get_connection
from app.database.migrations.runner import run_migrations
from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
    save_mullen_assessment,
)
from app.database.repositories.patients import create_patient
from app.database.schema import SCHEMA_SQL

CONTEXT = {
    "assessment_date": "2025-03-01",
    "scoring_date_of_birth": "2025-01-01",
    "confidence_level": 90,
    "age_calculation": "calendar",
}


def test_legacy_save_preserves_existing_scoring_context(temp_database):
    patient_id = create_patient("CONTEXT")
    save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 3}}, context=CONTEXT
    )
    save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 4}})
    assert get_mullen_assessment_context(patient_id) == CONTEXT


def test_failed_score_write_rolls_back_context_and_scores(temp_database):
    patient_id = create_patient("ATOMIC-MULLEN")
    save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 3}}, context=CONTEXT
    )
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_mullen BEFORE UPDATE ON mullen_scores "
            "BEGIN SELECT RAISE(ABORT, 'score write rejected'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="score write rejected"):
        save_mullen_assessment(
            patient_id,
            {"gross_motor": {"raw_score": 5}},
            context={**CONTEXT, "confidence_level": 95},
        )
    assert get_mullen_assessment_context(patient_id) == CONTEXT
    assert get_mullen_assessment(patient_id)["gross_motor"]["raw_score"] == 3


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confidence_level", 80),
        ("age_calculation", "unknown"),
        ("assessment_date", "bad"),
        ("assessment_date", "2024-01-01"),
    ],
)
def test_invalid_context_does_not_create_assessment(temp_database, field, value):
    patient_id = create_patient("INVALID-CONTEXT")
    with pytest.raises(ValueError):
        save_mullen_assessment(patient_id, {}, context={**CONTEXT, field: value})
    assert get_mullen_assessment_context(patient_id) == {}


def test_version_seven_upgrade_preserves_legacy_mullen_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "mullen-v7.db")
    old_schema = SCHEMA_SQL
    for column in (
        "    assessment_date TEXT,\n",
        "    scoring_date_of_birth TEXT,\n",
        "    confidence_level INTEGER,\n",
        "    age_calculation TEXT,\n",
    ):
        old_schema = old_schema.replace(column, "")
    with get_connection() as connection:
        connection.executescript(old_schema)
        connection.execute("PRAGMA user_version = 7")
    patient_id = create_patient("LEGACY-MULLEN")
    save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 3, "t_score": 48}})
    run_migrations()
    run_migrations()
    assert get_mullen_assessment(patient_id)["gross_motor"]["t_score"] == 48
    assert all(
        value is None for value in get_mullen_assessment_context(patient_id).values()
    )
