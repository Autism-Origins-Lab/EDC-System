# tests/test_form_queries.py
from app.database.connection import get_connection
from app.database.queries.forms import (
    get_mullen_assessment,
    get_telephone_screening,
    save_mullen_assessment,
    save_telephone_screening,
)
from app.database.queries.patients import create_patient, list_patients


def test_save_and_load_telephone_screening(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "Yes", "screener": "RA One"})
    form = get_telephone_screening(patient_id)
    assert form["eligibility"] == "Yes"
    assert form["screener"] == "RA One"

def test_saving_telephone_screening_twice_updates_existing_row(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "No"})
    save_telephone_screening(patient_id, {"eligibility": "Yes"})
    assert get_telephone_screening(patient_id)["eligibility"] == "Yes"

def test_patient_dashboard_reflects_form_status(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "Yes", "screener": "RA One"})
    assert list_patients()[0]["eligibility"] == "Yes"


def test_ineligibility_comment_is_saved_and_shown_on_dashboard(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(
        patient_id,
        {"eligibility": "No", "eligibility_comment": "Age is outside the range"},
    )

    assert get_telephone_screening(patient_id)["eligibility_comment"] == "Age is outside the range"
    assert list_patients()[0]["comment"] == "Age is outside the range"


def test_save_mullen_assessment_stores_scores_by_domain(temp_database):
    patient_id = create_patient("1001")
    scores = {
        "gross_motor": {
            "raw_score": 10,
            "t_score": 40,
            "band_of_error": 2.5,
            "percentile_rank": 16,
            "descriptive_category": "Below average",
            "age_equivalence": "12 months",
        },
        "visual_reception": {"raw_score": 20},
        "fine_motor": {"raw_score": 30},
        "receptive_language": {"raw_score": 40},
        "expressive_language": {"raw_score": 50},
    }

    save_mullen_assessment(patient_id, scores)

    with get_connection() as connection:
        assessments = connection.execute(
            "SELECT * FROM mullen_assessments WHERE patient_id = ?",
            (patient_id,),
        ).fetchall()
        rows = connection.execute(
            """
            SELECT ms.*
            FROM mullen_scores ms
            JOIN mullen_assessments ma
              ON ma.id = ms.mullen_assessments_id
            WHERE ma.patient_id = ?
            """,
            (patient_id,),
        ).fetchall()

    saved_scores = {row["domain"]: dict(row) for row in rows}
    assert len(assessments) == 1
    assert len(saved_scores) == 5
    assert saved_scores["gross_motor"]["raw_score"] == 10
    assert saved_scores["gross_motor"]["t_score"] == 40
    assert saved_scores["gross_motor"]["band_of_error"] == 2.5
    assert saved_scores["gross_motor"]["descriptive_category"] == "Below average"
    assert saved_scores["expressive_language"]["raw_score"] == 50


def test_save_mullen_assessment_updates_existing_domain(temp_database):
    patient_id = create_patient("1001")
    save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 10}})

    save_mullen_assessment(patient_id, {"gross_motor": {"raw_score": 99}})

    with get_connection() as connection:
        assessment_count = connection.execute(
            "SELECT COUNT(*) FROM mullen_assessments WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()[0]
        score_rows = connection.execute(
            """
            SELECT ms.raw_score
            FROM mullen_scores ms
            JOIN mullen_assessments ma
              ON ma.id = ms.mullen_assessments_id
            WHERE ma.patient_id = ? AND ms.domain = 'gross_motor'
            """,
            (patient_id,),
        ).fetchall()

    assert assessment_count == 1
    assert len(score_rows) == 1
    assert score_rows[0]["raw_score"] == 99


def test_get_mullen_assessment_returns_scores_by_domain(temp_database):
    patient_id = create_patient("1001")
    save_mullen_assessment(
        patient_id,
        {
            "gross_motor": {
                "raw_score": 10,
                "t_score": 40,
                "band_of_error": 2.5,
                "percentile_rank": 16,
                "descriptive_category": "Below average",
                "age_equivalence": "12 months",
            },
            "visual_reception": {"raw_score": 20},
        },
    )

    result = get_mullen_assessment(patient_id)

    assert set(result) == {"gross_motor", "visual_reception"}
    assert result["gross_motor"]["raw_score"] == 10
    assert result["gross_motor"]["t_score"] == 40
    assert result["gross_motor"]["band_of_error"] == 2.5
    assert result["gross_motor"]["descriptive_category"] == "Below average"
    assert result["gross_motor"]["age_equivalence"] == "12 months"
    assert result["visual_reception"]["raw_score"] == 20
