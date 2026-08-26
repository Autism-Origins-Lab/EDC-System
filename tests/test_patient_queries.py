# tests/test_patient_queries.py
import pytest

from app.database.queries.patients import (
    create_patient,
    get_patient,
    list_patients,
    search_patients,
    update_patient,
)


def test_create_patient_writes_record(temp_database):
    patient_id = create_patient("1001")
    assert get_patient(patient_id)["subject_id"] == "1001"

def test_create_patient_rejects_empty_subject_id(temp_database):
    with pytest.raises(ValueError):
        create_patient("   ")

def test_create_patient_rejects_duplicate_subject_id(temp_database):
    create_patient("1001")
    with pytest.raises(ValueError):
        create_patient("1001")

def test_update_patient_changes_allowed_fields(temp_database):
    patient_id = create_patient("1001")
    update_patient(patient_id, {"child_name": "Alex Test", "race": "Prefer not to answer"})
    patient = get_patient(patient_id)
    assert patient["child_name"] == "Alex Test"
    assert patient["race"] == "Prefer not to answer"

def test_list_patients_returns_dashboard_rows(temp_database):
    create_patient("1001")
    assert list_patients()[0]["subject_id"] == "1001"

def test_search_patients_matches_subject_id(temp_database):
    create_patient("1001")
    assert search_patients("1001")[0]["subject_id"] == "1001"