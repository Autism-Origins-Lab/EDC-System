import pytest
from PySide6.QtCore import Qt

from app.database.repositories.forms import (
    get_family_medical_history,
    get_medical_history,
    get_screening_questionnaire,
    save_family_medical_history,
    save_medical_history,
    save_screening_questionnaire,
)
from app.database.repositories.patients import create_patient
from app.ui.forms.family_medical_history_view import FamilyMedicalHistoryView
from app.ui.forms.medical_history_view import MedicalHistoryView
from app.ui.forms.screening_questionnaire_view import ScreeningQuestionnaireView

FORM_CASES = [
    (
        MedicalHistoryView,
        save_medical_history,
        get_medical_history,
        {
            "seen_neurologist": "seen_neurologist_input",
            "head_injury": "head_injury_input",
            "genetic_abnormalities": "genetic_abnormalities_input",
            "seizure_epileptic_attack": "seizure_epileptic_attack_input",
            "pregnancy_complications": "pregnancy_complications_input",
        },
    ),
    (
        FamilyMedicalHistoryView,
        save_family_medical_history,
        get_family_medical_history,
        {
            "family_psychiatric": "family_psychiatric_input",
            "parent_autism": "parent_autism_input",
            "parent_schizophrenia": "parent_schizophrenia_input",
            "parent_learning_disability": "parent_learning_disability_input",
            "parent_substance_abuse": "parent_substance_abuse_input",
            "has_siblings": "has_siblings_input",
            "sibling_autism": "sibling_autism_input",
            "sibling_adhd": "sibling_adhd_input",
            "same_father_as_older_sibling": "same_father_input",
            "same_mother_as_older_sibling": "same_mother_input",
        },
    ),
    (
        ScreeningQuestionnaireView,
        save_screening_questionnaire,
        get_screening_questionnaire,
        {
            "biological_mother": "biological_mother_input",
            "biological_father": "biological_father_input",
            "research_participation": "research_participation_input",
        },
    ),
]


@pytest.mark.parametrize("view_type,save,get,fields", FORM_CASES)
def test_untouched_answers_stay_null_after_save_and_reopen(
    temp_database, qtbot, view_type, save, get, fields
):
    patient_id = create_patient("UNANSWERED")
    view = view_type(patient_id)
    qtbot.addWidget(view)
    assert all(view.collect_data()[field] is None for field in fields)
    assert view.save(show_confirmation=False)
    assert all(get(patient_id)[field] is None for field in fields)
    reopened = view_type(patient_id)
    qtbot.addWidget(reopened)
    assert all(
        getattr(reopened, name).currentText() == "Not answered"
        for name in fields.values()
    )


@pytest.mark.parametrize("view_type,save,get,fields", FORM_CASES)
@pytest.mark.parametrize("offset", [0, 1, 2])
def test_existing_yes_no_and_null_answers_survive_loading_and_resaving(
    temp_database, qtbot, view_type, save, get, fields, offset
):
    patient_id = create_patient("EXISTING-ANSWERS")
    expected = {
        field: (None, 0, 1)[(index + offset) % 3] for index, field in enumerate(fields)
    }
    save(patient_id, expected)
    view = view_type(patient_id)
    qtbot.addWidget(view)
    for field, name in fields.items():
        assert getattr(view, name).value() == expected[field]
        assert (
            getattr(view, name).currentText()
            == {None: "Not answered", 0: "No", 1: "Yes"}[expected[field]]
        )
    assert view.save(show_confirmation=False)
    actual = get(patient_id)
    assert {field: actual[field] for field in fields} == expected


@pytest.mark.parametrize("view_type,save,get,fields", FORM_CASES)
def test_user_can_choose_no_then_clear_an_answer(
    temp_database, qtbot, view_type, save, get, fields
):
    patient_id = create_patient("CLEAR-ANSWER")
    view = view_type(patient_id)
    qtbot.addWidget(view)
    field, name = next(iter(fields.items()))
    control = getattr(view, name)
    qtbot.keyClick(control, Qt.Key.Key_Down)
    assert control.currentText() == "Yes"
    qtbot.keyClick(control, Qt.Key.Key_Down)
    assert control.currentText() == "No"
    assert view.save(show_confirmation=False)
    assert get(patient_id)[field] == 0
    qtbot.keyClick(control, Qt.Key.Key_Home)
    assert control.currentText() == "Not answered"
    assert view.save(show_confirmation=False)
    assert get(patient_id)[field] is None
