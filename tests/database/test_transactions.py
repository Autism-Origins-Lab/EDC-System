import sqlite3
from contextlib import closing

import pytest

from app.database.connection import get_connection, transaction
from app.database.repositories.forms import get_medical_history, save_medical_history
from app.database.repositories.patients import (
    complete_patient_form,
    create_patient,
    get_patient,
    update_patient,
    update_patient_form,
)


def test_repository_calls_commit_only_at_outer_transaction_exit(temp_database):
    patient_id = create_patient("TRANSACTION")
    complete_patient_form(patient_id, "Jordan Staff")

    with transaction() as connection:
        update_patient(patient_id, {"child_name": "Changed"})
        with transaction() as nested:
            assert nested is connection
            save_medical_history(patient_id, {"general_health": "Healthy"})
            update_patient_form(patient_id, "Pending")
        with get_connection() as reader:
            assert reader is connection
        assert get_patient(patient_id)["child_name"] == "Changed"
        with closing(sqlite3.connect(temp_database)) as observer:
            assert observer.execute(
                "SELECT child_name, form_status FROM patients WHERE id = ?",
                (patient_id,),
            ).fetchone() == (None, "Complete")
            assert observer.execute("SELECT * FROM medical_histories").fetchall() == []

    assert get_patient(patient_id)["child_name"] == "Changed"
    assert get_patient(patient_id)["form_status"] == "Pending"
    assert get_medical_history(patient_id)["general_health"] == "Healthy"


def test_failure_after_status_write_rolls_back_all_writes_and_releases_scope(
    temp_database,
):
    patient_id = create_patient("ROLLBACK")
    complete_patient_form(patient_id, "Jordan Staff")

    with pytest.raises(OSError, match="save interrupted"), transaction():
        update_patient(patient_id, {"child_name": "Must roll back"})
        save_medical_history(patient_id, {"general_health": "Must roll back"})
        update_patient_form(patient_id, "Pending")
        raise OSError("save interrupted")

    assert get_patient(patient_id)["child_name"] is None
    assert get_patient(patient_id)["form_status"] == "Complete"
    assert get_medical_history(patient_id) is None
    # Subsequent standalone operations must not reuse a closed transaction connection.
    update_patient(patient_id, {"child_name": "Independent save"})
    assert get_patient(patient_id)["child_name"] == "Independent save"
