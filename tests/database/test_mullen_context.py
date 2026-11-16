import sqlite3

import pytest

from app import config
from app.database.connection import get_connection
from app.database.migrations.runner import run_migrations
from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
    list_mullen_assessments,
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
    assessment_id = save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 3}}, context=CONTEXT
    )
    save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 4}}, assessment_id=assessment_id
    )
    assert get_mullen_assessment_context(patient_id) == CONTEXT


def test_failed_score_write_rolls_back_context_and_scores(temp_database):
    patient_id = create_patient("ATOMIC-MULLEN")
    assessment_id = save_mullen_assessment(
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
            assessment_id=assessment_id,
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
        "    assessment_number INTEGER NOT NULL DEFAULT 0,\n",
        "    saved_order INTEGER NOT NULL DEFAULT 0,\n",
    ):
        old_schema = old_schema.replace(column, "")
    with get_connection() as connection:
        connection.executescript(old_schema)
        connection.execute("PRAGMA user_version = 7")
    patient_id = create_patient("LEGACY-MULLEN")
    with get_connection() as connection:
        assessment_id = connection.execute(
            "INSERT INTO mullen_assessments(patient_id) VALUES (?)", (patient_id,)
        ).lastrowid
        connection.execute(
            "INSERT INTO mullen_scores(mullen_assessments_id, domain, raw_score, t_score) "
            "VALUES (?, 'gross_motor', 3, 48)", (assessment_id,),
        )
    run_migrations()
    run_migrations()
    assert get_mullen_assessment(patient_id)["gross_motor"]["t_score"] == 48
    assert all(
        value is None for value in get_mullen_assessment_context(patient_id).values()
    )
    assert list_mullen_assessments(patient_id)[0]["assessment_number"] == 1


def test_separate_summaries_and_latest_save_order(temp_database):
    patient_id = create_patient("HISTORY")
    first = save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 3}}, context=CONTEXT)
    second = save_mullen_assessment(
        patient_id, {"gross_motor": {"raw_score": 0}},
        context={**CONTEXT, "assessment_date": "2025-02-01"},
    )
    assert get_mullen_assessment(patient_id)["gross_motor"]["raw_score"] == 0
    assert get_mullen_assessment(patient_id, first)["gross_motor"]["raw_score"] == 3
    save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 4}}, assessment_id=first)
    summaries = list_mullen_assessments(patient_id)
    assert [(row["id"], row["assessment_number"]) for row in summaries] == [(first, 1), (second, 2)]
    assert get_mullen_assessment(patient_id)["gross_motor"]["raw_score"] == 4
    assert get_mullen_assessment_context(patient_id, second)["assessment_date"] == "2025-02-01"


def test_summary_ids_are_scoped_to_patient(temp_database):
    first_patient = create_patient("OWNER")
    second_patient = create_patient("OTHER")
    assessment_id = save_mullen_assessment(first_patient, {}, context=CONTEXT)
    with pytest.raises(ValueError, match="does not belong"):
        save_mullen_assessment(second_patient, {}, assessment_id=assessment_id, context=CONTEXT)
    assert get_mullen_assessment(second_patient, assessment_id) == {}
    assert get_mullen_assessment_context(second_patient, assessment_id) == {}
    assert list_mullen_assessments(second_patient) == []


def test_blank_summary_requires_date_but_not_scoring_options(temp_database):
    patient_id = create_patient("NOT-ADMINISTERED")
    context = dict.fromkeys(CONTEXT)
    with pytest.raises(ValueError):
        save_mullen_assessment(patient_id, {}, context=context)
    with pytest.raises(ValueError, match="Date completed"):
        save_mullen_assessment(patient_id, {})
    context["assessment_date"] = "2025-03-01"
    assessment_id = save_mullen_assessment(patient_id, {}, context=context)
    assert get_mullen_assessment_context(patient_id, assessment_id) == context


def test_version_eight_upgrade_numbers_history_without_changing_scores_or_dates():
    from app.database.migrations.versions import v009_mullen_summaries

    old_schema = SCHEMA_SQL
    for column in ("assessment_number", "saved_order"):
        old_schema = old_schema.replace(f"    {column} INTEGER NOT NULL DEFAULT 0,\n", "")
    with sqlite3.connect(":memory:") as connection:
        connection.executescript(old_schema)
        connection.executemany("INSERT INTO patients(id, subject_id) VALUES (?, ?)", [(1, "A"), (2, "B")])
        connection.executemany(
            "INSERT INTO mullen_assessments(id, patient_id, assessment_date, updated_at) VALUES (?, ?, ?, ?)",
            [(1, 1, None, "2026-11-16"), (2, 1, "2025-03-01", "2026-11-15"), (3, 2, None, "2026-11-14")],
        )
        connection.execute(
            "INSERT INTO mullen_scores(mullen_assessments_id, domain, raw_score, t_score) "
            "VALUES (1, 'gross_motor', 3, 48)"
        )
        v009_mullen_summaries.upgrade(connection)
        v009_mullen_summaries.upgrade(connection)
        assert connection.execute(
            "SELECT id, assessment_number, saved_order, assessment_date FROM mullen_assessments ORDER BY id"
        ).fetchall() == [(1, 1, 2, None), (2, 2, 1, "2025-03-01"), (3, 1, 1, None)]
        assert connection.execute("SELECT raw_score, t_score FROM mullen_scores").fetchall() == [(3, 48)]
