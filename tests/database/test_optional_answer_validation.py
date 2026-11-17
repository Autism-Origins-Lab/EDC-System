"""Reject invalid Yes/No values before changing saved form answers."""

import pytest

from app.database.repositories.forms import get_medical_history, save_medical_history
from app.database.repositories.patients import create_patient


@pytest.mark.parametrize("invalid", [2, -1, "0", "False", "", 0.0, []])
def test_invalid_boolean_does_not_modify_saved_answers(temp_database, invalid):
    patient_id = create_patient("INVALID-BOOLEAN")
    save_medical_history(
        patient_id, {"general_health": "Original", "seen_neurologist": None}
    )
    before = get_medical_history(patient_id)
    with pytest.raises(ValueError, match="Yes, No, or unanswered"):
        save_medical_history(
            patient_id, {"general_health": "Changed", "seen_neurologist": invalid}
        )
    assert get_medical_history(patient_id) == before
