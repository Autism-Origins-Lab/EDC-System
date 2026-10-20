from app.database.connection import get_connection
from app.database.queries.forms import (
    get_family_medical_history,
    list_siblings,
    save_family_medical_history,
    save_siblings,
)
from app.database.queries.patients import create_patient

MAYA = {"name": "Maya", "age": "4", "same_bio_father": 1, "same_bio_mother": 1,
        "adopted": 0, "diagnosis": ""}
LEO = {"name": "Leo", "age": "18 months", "same_bio_father": 0, "same_bio_mother": None,
       "adopted": 1, "diagnosis": "ADHD"}


def test_save_and_list_siblings(temp_database):
    patient_id = create_patient("1001")
    save_siblings(patient_id, [MAYA, LEO])
    assert list_siblings(patient_id) == [MAYA, LEO]


def test_unknown_parent_stays_none(temp_database):
    patient_id = create_patient("1001")
    save_siblings(patient_id, [LEO])
    assert list_siblings(patient_id)[0]["same_bio_mother"] is None


def test_saving_again_replaces_the_list(temp_database):
    patient_id = create_patient("1001")
    save_siblings(patient_id, [MAYA, LEO])
    save_siblings(patient_id, [LEO])
    assert list_siblings(patient_id) == [LEO]
    save_siblings(patient_id, [])
    assert list_siblings(patient_id) == []


def test_siblings_belong_to_one_patient(temp_database):
    first_id = create_patient("1001")
    second_id = create_patient("1002")
    save_siblings(first_id, [MAYA])
    save_siblings(second_id, [LEO])
    save_siblings(first_id, [])
    assert list_siblings(second_id) == [LEO]


def test_deleting_patient_deletes_their_siblings(temp_database):
    patient_id = create_patient("1001")
    save_siblings(patient_id, [MAYA])
    with get_connection() as connection:
        connection.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    assert list_siblings(patient_id) == []


def test_sibling_type_columns_save_and_load(temp_database):
    patient_id = create_patient("1001")
    save_family_medical_history(
        patient_id, {"sibling_autism": 1, "sibling_autism_half": 1, "sibling_adhd_full": 0}
    )
    saved = get_family_medical_history(patient_id)
    assert saved["sibling_autism_half"] == 1
    assert saved["sibling_adhd_full"] == 0
