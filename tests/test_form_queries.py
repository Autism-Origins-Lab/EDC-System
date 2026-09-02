# tests/test_form_queries.py
from app.database.queries.forms import get_telephone_screening, save_telephone_screening
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