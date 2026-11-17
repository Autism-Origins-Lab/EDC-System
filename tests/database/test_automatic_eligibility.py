from datetime import date, timedelta

import pytest

from app.database.repositories.forms import (
    get_telephone_screening,
    save_screening_questionnaire,
    save_telephone_screening,
)
from app.database.repositories.patients import (
    create_patient,
    ineligibility_reason,
    list_patients,
    update_patient,
)

TODAY = date(2026, 4, 1)
RECENT_BIRTHDAY = (date.today() - timedelta(days=30)).isoformat()


@pytest.mark.parametrize("age, gest_age, dob, expected", [
    # Born, eligible
    (None, "38", "2026-02-15", None),
    (None, "N/A", "2026-01-02", None),            # 2 months 30 days old
    # Born, too old (by date of birth)
    (None, "38", "2026-01-01", "Age is 3 months or older."),
    # Born, too old (by typed age, no date of birth)
    ("3", None, None, "Age is 3 months or older."),
    ("2.75", None, None, None),
    # Born preterm
    (None, "36", "2026-03-01", "Born at or before 37 weeks gestation."),
    ("1", "36", None, "Born at or before 37 weeks gestation."),
    (None, "30", "2025-12-01", "Age is 3 months or older. Born at or before 37 weeks gestation."),
    (None, "37", "2026-03-01", "Born at or before 37 weeks gestation."),
    ("1", "37.5", None, None),
    # Not born yet: no rules apply
    (None, "30", "2026-06-01", None),
    (None, "30", None, None),
    # N/A or blank never marks ineligible
    ("N/A", "N/A", None, None),
    ("", "n/a", "2026-03-01", None),
    # Older records use MM/DD/YYYY
    (None, "38", "01/01/2026", "Age is 3 months or older."),
])
def test_ineligibility_reason(age, gest_age, dob, expected):
    assert ineligibility_reason(age, gest_age, dob, TODAY) == expected


def test_preterm_born_patient_marked_ineligible_with_comment(temp_database):
    patient_id = create_patient("1001")
    update_patient(patient_id, {"date_of_birth": RECENT_BIRTHDAY})
    save_telephone_screening(
        patient_id,
        {"eligibility": "Yes", "gestational": "35"},
    )

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Born at or before 37 weeks gestation."
    assert list_patients()[0]["comment"] == "Born at or before 37 weeks gestation."


def test_unborn_patient_with_low_gestational_age_is_not_marked(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "Yes", "gestational": "30"})

    assert get_telephone_screening(patient_id)["eligibility"] == "Yes"


def test_questionnaire_age_marks_patient_ineligible(temp_database):
    patient_id = create_patient("1001")
    save_screening_questionnaire(patient_id, {"age": "5"})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Age is 3 months or older."


def test_na_gestational_age_leaves_eligibility_alone(temp_database):
    patient_id = create_patient("1001")
    update_patient(patient_id, {"date_of_birth": RECENT_BIRTHDAY})
    save_telephone_screening(
        patient_id,
        {"eligibility": "Yes", "gestational": "N/A"},
    )

    assert get_telephone_screening(patient_id)["eligibility"] == "Yes"


def test_age_is_measured_from_date_of_birth_to_today(temp_database):
    patient_id = create_patient("1001")
    update_patient(patient_id, {"date_of_birth": (date.today() - timedelta(days=100)).isoformat()})
    save_telephone_screening(patient_id, {"eligibility": "Yes", "gestational": "39"})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Age is 3 months or older."


def test_saving_date_of_birth_from_overview_marks_patient_ineligible(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "Yes"})
    update_patient(patient_id, {"date_of_birth": "2007-09-27"})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Age is 3 months or older."


def test_fixing_birthday_resets_automatic_ineligibility_to_not_evaluated(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(patient_id, {"eligibility": "Yes", "gestational": ""})
    update_patient(patient_id, {"date_of_birth": "2007-09-27"})
    assert get_telephone_screening(patient_id)["eligibility"] == "No"

    update_patient(patient_id, {"date_of_birth": RECENT_BIRTHDAY})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "Not evaluated"
    assert screening["eligibility_comment"] == ""
    assert list_patients()[0]["eligibility"] == "Not evaluated"


def test_staff_entered_ineligibility_is_not_reset(temp_database):
    patient_id = create_patient("1001")
    save_telephone_screening(
        patient_id,
        {"eligibility": "No", "eligibility_comment": "Unable to attend visits"},
    )
    update_patient(patient_id, {"date_of_birth": RECENT_BIRTHDAY})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Unable to attend visits"


def test_staff_comment_takes_priority_over_automatic_reason(temp_database):
    patient_id = create_patient("1001")
    update_patient(patient_id, {"date_of_birth": RECENT_BIRTHDAY})
    save_telephone_screening(
        patient_id,
        {"eligibility": "No", "eligibility_comment": "Unable to attend visits", "gestational": "35"},
    )
    update_patient(patient_id, {"date_of_birth": "2007-09-27"})

    screening = get_telephone_screening(patient_id)
    assert screening["eligibility"] == "No"
    assert screening["eligibility_comment"] == "Unable to attend visits"


def test_not_evaluated_filter_ignores_case(temp_database):
    from app.database.connection import get_connection

    patient_id = create_patient("1001")
    create_patient("1002")
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO telephone_screenings (patient_id, eligibility) VALUES (?, ' not EVALUATED ')",
            (patient_id,),
        )

    assert len(list_patients(eligibility_filter="Not Evaluated Only")) == 2
