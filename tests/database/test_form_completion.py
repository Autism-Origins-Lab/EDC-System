import sqlite3

import pytest

from app.database.connection import get_connection
from app.database.repositories.forms import (
    get_telephone_screening,
    save_telephone_screening,
)
from app.database.repositories.patients import (
    complete_patient_form,
    create_patient,
    get_patient,
)


@pytest.mark.parametrize("name", [None, "", "   "])
def test_completion_requires_screener(temp_database, name):
    patient_id = create_patient("NO-SCREENER")
    with pytest.raises(ValueError, match="Screener name is required"):
        complete_patient_form(patient_id, name)
    assert get_patient(patient_id)["form_status"] == "Pending"
    assert get_telephone_screening(patient_id) is None


def test_completion_preserves_screening_and_ignores_eligibility(temp_database):
    patient_id = create_patient("COMPLETE")
    save_telephone_screening(
        patient_id,
        {"eligibility": "No", "screener": "Old", "eligibility_comment": "Reason"},
    )
    complete_patient_form(patient_id, "  Jordan Staff  ")
    assert get_patient(patient_id)["form_status"] == "Complete"
    screening = get_telephone_screening(patient_id)
    assert screening["screener"] == "Jordan Staff"
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Reason"


def test_failed_screener_write_rolls_back_completion(temp_database):
    patient_id = create_patient("ATOMIC-COMPLETE")
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_screener BEFORE INSERT ON telephone_screenings "
            "BEGIN SELECT RAISE(ABORT, 'screener failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="screener failure"):
        complete_patient_form(patient_id, "Jordan Staff")
    assert get_patient(patient_id)["form_status"] == "Pending"
    assert get_telephone_screening(patient_id) is None


def test_missing_patient_does_not_create_screening(temp_database):
    with pytest.raises(ValueError, match="Patient does not exist"):
        complete_patient_form(999, "Jordan Staff")
