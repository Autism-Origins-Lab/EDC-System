import pytest
from PySide6.QtWidgets import QMessageBox

from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
)
from app.database.repositories.patients import create_patient, update_patient
from app.services.preferences import DEFAULT_PREFERENCES
from app.ui.dialogs.patient_detail_view import PatientDetailView
from app.ui.forms import mullen_view


@pytest.fixture
def workspace(temp_database, qtbot, monkeypatch):
    monkeypatch.setattr(
        mullen_view, "load_preferences", lambda: DEFAULT_PREFERENCES.copy()
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard
    )
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[-1]))
    patient_id = create_patient("MULLEN-UI")
    update_patient(patient_id, {"date_of_birth": "2025-01-01"})
    view = PatientDetailView(patient_id, preferences=DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(view)
    view.show()
    view._show_step(6)
    view.warnings = warnings
    return view


def configure(page):
    page.assessment_date_input.setText("2025-03-01")
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(90))
    page.age_calculation_combo.setCurrentIndex(
        page.age_calculation_combo.findData("calendar")
    )


def test_typing_raw_score_fills_read_only_results(workspace, qtbot):
    page = workspace.mullen_view
    configure(page)
    qtbot.keyClicks(page.raw_score_inputs[0], "3")
    assert page.t_score_inputs[0].text() == "37"
    assert page.error_inputs[0].text() == "9"
    assert page.percentile_inputs[0].text() == "10"
    assert page.category_inputs[0].text() == "Below Average"
    assert page.age_equivalent_inputs[0].text() == ""
    assert "2 months, 0 days" in page.age_label.text()
    for inputs in (
        page.t_score_inputs,
        page.error_inputs,
        page.percentile_inputs,
        page.category_inputs,
    ):
        assert inputs[0].isReadOnly()
    assert workspace.has_unsaved_changes()


def test_context_changes_recalculate_and_clear_invalid_results(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(95))
    assert page.error_inputs[0].text() == "11"
    assert page.t_score_inputs[0].text() == "37"
    page.assessment_date_input.setText("2025-04-01")
    assert page.t_score_inputs[0].text() == "31"
    page.assessment_date_input.setText("2025-06-01")
    assert page.t_score_inputs[0].text() == ""
    assert "No handbook age band" in page.scoring_status.text()
    assert not workspace.save_current_section()
    assert get_mullen_assessment(workspace.patient_id) == {}


def test_blank_and_out_of_range_raw_inputs_clear_previous_results(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    page.raw_score_inputs[0].clear()
    assert page.t_score_inputs[0].text() == ""
    assert page.category_inputs[0].text() == ""
    page.raw_score_inputs[0].setText("99")
    assert page.error_inputs[0].text() == ""
    assert "No handbook conversion" in page.scoring_status.text()
    assert not workspace.save_current_section()


def test_save_reopen_and_discard_preserve_scores_and_context(
    workspace, qtbot, monkeypatch
):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    assert not workspace.has_unsaved_changes()
    context = get_mullen_assessment_context(workspace.patient_id)
    assert context == {
        "assessment_date": "2025-03-01",
        "scoring_date_of_birth": "2025-01-01",
        "confidence_level": 90,
        "age_calculation": "calendar",
    }
    assert get_mullen_assessment(workspace.patient_id)["gross_motor"]["t_score"] == 37
    page.assessment_date_input.setText("2025-04-01")
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(95))
    page.raw_score_inputs[0].setText("5")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard
    )
    workspace.go_back()
    assert workspace.has_unsaved_changes()
    workspace.close()
    reopened = PatientDetailView(workspace.patient_id)
    qtbot.addWidget(reopened)
    assert reopened.mullen_view.t_score_inputs[0].text() == "37"
    assert reopened.mullen_view.assessment_date_input.text() == "2025-03-01"
    assert reopened.mullen_view.confidence_combo.currentData() == 90
    assert reopened.mullen_view.age_calculation_combo.currentData() == "calendar"


def test_failed_save_keeps_previous_database_values(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    original = get_mullen_assessment(workspace.patient_id)
    page.assessment_date_input.setText("2024-12-31")
    assert not workspace.save_current_section()
    assert "cannot precede" in page.scoring_status.text()
    assert get_mullen_assessment(workspace.patient_id) == original
    assert (
        get_mullen_assessment_context(workspace.patient_id)["assessment_date"]
        == "2025-03-01"
    )
    assert workspace.has_unsaved_changes()


def test_saved_dob_is_preserved_until_overview_dob_is_requested(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    update_patient(workspace.patient_id, {"date_of_birth": "2025-02-01"})
    workspace._reload_view(6)
    assert page.date_of_birth_input.text() == "2025-01-01"
    assert page.t_score_inputs[0].text() == "37"
    assert "Overview DOB differs" in page.scoring_status.text()
    page.use_overview_dob_button.click()
    assert page.date_of_birth_input.text() == "2025-02-01"
    assert page.t_score_inputs[0].text() == "48"
    assert workspace.has_unsaved_changes()
    assert workspace.save_current_section()
    assert (
        get_mullen_assessment_context(workspace.patient_id)["scoring_date_of_birth"]
        == "2025-02-01"
    )


@pytest.mark.parametrize("missing", ["birthday", "date", "confidence", "convention"])
def test_missing_required_context_blocks_save(workspace, missing):
    page = workspace.mullen_view
    configure(page)
    if missing == "birthday":
        page.date_of_birth_input.clear()
    elif missing == "date":
        page.assessment_date_input.clear()
    elif missing == "confidence":
        page.confidence_combo.setCurrentIndex(0)
    else:
        page.age_calculation_combo.setCurrentIndex(0)
    page.raw_score_inputs[0].setText("3")
    assert page.t_score_inputs[0].text() == ""
    assert not workspace.save_current_section()
    assert workspace.warnings


def test_date_format_preference_is_respected(temp_database, qtbot, monkeypatch):
    prefs = {**DEFAULT_PREFERENCES, "date_format": "MM/DD/YYYY"}
    monkeypatch.setattr(mullen_view, "load_preferences", lambda: prefs)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    patient_id = create_patient("MULLEN-DATE")
    update_patient(patient_id, {"date_of_birth": "2025-01-01"})
    page = mullen_view.MullenView(patient_id)
    qtbot.addWidget(page)
    assert page.date_of_birth_input.text() == "01/01/2025"
    page.assessment_date_input.setText("03/01/2025")
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(90))
    page.age_calculation_combo.setCurrentIndex(
        page.age_calculation_combo.findData("calendar")
    )
    page.raw_score_inputs[0].setText("3")
    assert page.t_score_inputs[0].text() == "37"
    assert page.save()
    assert get_mullen_assessment_context(patient_id)["assessment_date"] == "2025-03-01"
