import pytest
from PySide6.QtWidgets import QMessageBox

from app.database.connection import get_connection
from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
    list_mullen_assessments,
)
from app.database.repositories.patients import complete_patient_form, create_patient, update_patient
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
    page.assessment_date_input.setText("03-01-2025")
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


@pytest.mark.parametrize("unsupported_date", ["05-01-2025", "05-31-2025", "06-01-2025"])
def test_context_changes_recalculate_and_clear_invalid_results(workspace, unsupported_date):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(95))
    assert page.error_inputs[0].text() == "11"
    assert page.t_score_inputs[0].text() == "37"
    page.assessment_date_input.setText("04-01-2025")
    assert page.t_score_inputs[0].text() == "31"
    page.assessment_date_input.setText(unsupported_date)
    for inputs in (
        page.t_score_inputs,
        page.error_inputs,
        page.percentile_inputs,
        page.category_inputs,
    ):
        assert inputs[0].text() == ""
    assert page.raw_score_inputs[0].text() == "3"
    assert "No handbook age band" in page.scoring_status.text()
    assert not workspace.save_current_section()
    assert get_mullen_assessment(workspace.patient_id) == {}
    assert get_mullen_assessment_context(workspace.patient_id) == {}


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
    page.assessment_date_input.setText("04-01-2025")
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
    assert reopened.mullen_view.assessment_date_input.text() == "03-01-2025"
    assert reopened.mullen_view.confidence_combo.currentData() == 90
    assert reopened.mullen_view.age_calculation_combo.currentData() == "calendar"


def test_failed_save_keeps_previous_database_values(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    original = get_mullen_assessment(workspace.patient_id)
    page.assessment_date_input.setText("12-31-2024")
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
    assert page.date_of_birth_input.text() == "01-01-2025"
    assert page.t_score_inputs[0].text() == "37"
    assert "Overview DOB differs" in page.scoring_status.text()
    page.use_overview_dob_button.click()
    assert page.date_of_birth_input.text() == "02-01-2025"
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


def test_dates_are_typed_as_digits_only(temp_database, qtbot, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    patient_id = create_patient("MULLEN-DATE")
    update_patient(patient_id, {"date_of_birth": "2025-01-01"})
    page = mullen_view.MullenView(patient_id)
    qtbot.addWidget(page)
    assert page.date_of_birth_input.text() == "01-01-2025"
    qtbot.keyClicks(page.assessment_date_input, "03/0a1-2025")
    assert page.assessment_date_input.text() == "03-01-2025"
    page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(90))
    page.age_calculation_combo.setCurrentIndex(
        page.age_calculation_combo.findData("calendar")
    )
    page.raw_score_inputs[0].setText("3")
    assert page.t_score_inputs[0].text() == "37"
    assert page.save()
    assert get_mullen_assessment_context(patient_id)["assessment_date"] == "2025-03-01"


def test_new_summary_is_blank_and_saves_separately(workspace, qtbot):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    page.age_equivalent_inputs[0].setText("2")
    assert workspace.save_current_section()
    first_id = page.assessment_id
    page.new_summary_button.click()
    assert page.assessment_id is None
    assert page.date_of_birth_input.text() == "01-01-2025"
    assert page.assessment_date_input.text() == ""
    assert page.confidence_combo.currentData() is None
    assert page.age_calculation_combo.currentData() is None
    for inputs in (
        page.raw_score_inputs, page.t_score_inputs, page.error_inputs,
        page.percentile_inputs, page.category_inputs, page.age_equivalent_inputs,
    ):
        assert all(field.text() == "" for field in inputs.values())
    assert workspace.has_unsaved_changes()
    assert not workspace.save_current_section()  # Explicit new summaries require a date.
    page.assessment_date_input.setText("02-01-2025")
    assert workspace.save_current_section()  # Every raw score may remain blank.
    second_id = page.assessment_id
    assert second_id != first_id
    assert not workspace.has_unsaved_changes()
    assert page.assessment_combo.currentText() == "Mullen #2 — 02-01-2025"
    assert get_mullen_assessment(workspace.patient_id, first_id)["gross_motor"]["raw_score"] == 3
    assert all(score["raw_score"] is None for score in get_mullen_assessment(workspace.patient_id, second_id).values())
    reopened = PatientDetailView(workspace.patient_id)
    qtbot.addWidget(reopened)
    assert reopened.mullen_view.assessment_id == second_id  # Last saved, not latest assessment date.
    page.assessment_combo.setCurrentIndex(page.assessment_combo.findData(first_id))
    assert page.raw_score_inputs[0].text() == "3"
    assert page.age_equivalent_inputs[0].text() == "2"
    assert not workspace.has_unsaved_changes()  # Selecting is not an edit.
    page.assessment_date_input.setText("04-01-2025")
    page.raw_score_inputs[0].setText("0")
    assert workspace.save_current_section()
    assert page.assessment_combo.currentText() == "Mullen #1 — 04-01-2025"
    reopened_again = PatientDetailView(workspace.patient_id)
    qtbot.addWidget(reopened_again)
    assert reopened_again.mullen_view.assessment_id == first_id
    assert reopened_again.mullen_view.raw_score_inputs[0].text() == "0"
    assert len(list_mullen_assessments(workspace.patient_id)) == 2


def test_clearing_saved_scores_persists_and_review_shows_not_administered(workspace, qtbot):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    assessment_id = page.assessment_id
    page.assessment_date_input.clear()
    page.confidence_combo.setCurrentIndex(0)
    page.age_calculation_combo.setCurrentIndex(0)
    page.raw_score_inputs[0].clear()
    assert not workspace.save_current_section()
    assert get_mullen_assessment(workspace.patient_id, assessment_id)["gross_motor"]["raw_score"] == 3
    page.assessment_date_input.setText("03-01-2025")
    assert workspace.save_current_section()
    assert page.assessment_id == assessment_id
    assert len(list_mullen_assessments(workspace.patient_id)) == 1
    assert all(
        score[field] is None
        for score in get_mullen_assessment(workspace.patient_id, assessment_id).values()
        for field in ("raw_score", "t_score", "band_of_error", "percentile_rank", "descriptive_category")
    )
    context = get_mullen_assessment_context(workspace.patient_id, assessment_id)
    assert context["confidence_level"] is None
    assert context["age_calculation"] is None
    reopened = PatientDetailView(workspace.patient_id)
    qtbot.addWidget(reopened)
    assert reopened.mullen_view.raw_score_inputs[0].text() == ""
    reopened.summary_view.refresh_answers()
    answers = dict(dict(reopened.summary_view.answers)["Mullen assessment"])
    assert answers["Mullen #1 — 03-01-2025 / Gross Motor / Raw score"] == "Not administered"
    assert answers["Mullen #1 — 03-01-2025 / Gross Motor / T score"] == "N/A"


@pytest.mark.parametrize("choice", ["Save", "Discard", "Cancel"])
def test_switching_summaries_handles_unsaved_edits(workspace, monkeypatch, choice):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    first_id = page.assessment_id
    page.new_summary()
    configure(page)
    page.raw_score_inputs[0].setText("0")
    assert workspace.save_current_section()
    second_id = page.assessment_id
    page.raw_score_inputs[0].setText("5")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: getattr(QMessageBox.StandardButton, choice))
    page.assessment_combo.setCurrentIndex(page.assessment_combo.findData(first_id))
    assert page.assessment_id == (second_id if choice == "Cancel" else first_id)
    assert page.assessment_combo.currentData() == page.assessment_id
    assert workspace.has_unsaved_changes() == (choice == "Cancel")
    expected_raw = 5 if choice == "Save" else 0
    assert get_mullen_assessment(workspace.patient_id, second_id)["gross_motor"]["raw_score"] == expected_raw
    assert page.raw_score_inputs[0].text() == ("5" if choice == "Cancel" else "3")


def test_failed_validation_prevents_switch_or_new_summary(workspace, monkeypatch):
    page = workspace.mullen_view
    configure(page)
    assert workspace.save_current_section()
    first_id = page.assessment_id
    page.new_summary()
    configure(page)
    assert workspace.save_current_section()
    second_id = page.assessment_id
    page.assessment_date_input.clear()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save)
    page.assessment_combo.setCurrentIndex(page.assessment_combo.findData(first_id))
    assert page.assessment_id == second_id
    assert page.assessment_combo.currentData() == second_id
    page.new_summary_button.click()
    assert page.assessment_id == second_id
    assert page.assessment_date_input.text() == ""
    assert workspace.has_unsaved_changes()


def test_new_summary_save_and_discard_prompts(workspace, monkeypatch):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    page.new_summary_button.click()
    assert page.raw_score_inputs[0].text() == "3"
    assert list_mullen_assessments(workspace.patient_id) == []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save)
    page.new_summary_button.click()
    summaries = list_mullen_assessments(workspace.patient_id)
    assert len(summaries) == 1
    assert get_mullen_assessment(workspace.patient_id, summaries[0]["id"])["gross_motor"]["raw_score"] == 3
    assert page.assessment_id is None
    assert page.raw_score_inputs[0].text() == ""
    workspace.go_back()
    workspace._show_step(6)
    assert page.assessment_id is None  # Returning preserves the new draft.
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
    page.assessment_combo.setCurrentIndex(page.assessment_combo.findData(summaries[0]["id"]))
    assert page.assessment_id == summaries[0]["id"]  # Fixture chooses Discard.


def test_review_includes_each_saved_summary(workspace):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("0")
    assert workspace.save_current_section()
    page.new_summary()
    page.assessment_date_input.setText("04-01-2025")
    assert workspace.save_current_section()
    workspace.summary_view.refresh_answers()
    answers = dict(dict(workspace.summary_view.answers)["Mullen assessment"])
    assert answers["Mullen #1 — 03-01-2025 / Gross Motor / Raw score"] == "0"
    assert answers["Mullen #2 — 04-01-2025 / Gross Motor / Raw score"] == "Not administered"


@pytest.mark.parametrize("new_summary", [False, True])
def test_failed_transaction_keeps_summary_draft_and_allows_retry(workspace, new_summary):
    page = workspace.mullen_view
    configure(page)
    page.raw_score_inputs[0].setText("3")
    assert workspace.save_current_section()
    first_id = page.assessment_id
    original_summaries = list_mullen_assessments(workspace.patient_id)
    original_scores = get_mullen_assessment(workspace.patient_id, first_id)
    if new_summary:
        page.new_summary()
    else:
        page.raw_score_inputs[0].clear()
        page.confidence_combo.setCurrentIndex(0)
        page.age_calculation_combo.setCurrentIndex(0)
    page.assessment_date_input.setText("04-01-2025")
    draft = page.input_state()
    complete_patient_form(workspace.patient_id, "Example Screener")
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_pending BEFORE UPDATE OF form_status ON patients "
            "WHEN NEW.form_status = 'Pending' "
            "BEGIN SELECT RAISE(ABORT, 'status write rejected'); END"
        )
    assert not workspace.save_current_section()
    assert list_mullen_assessments(workspace.patient_id) == original_summaries
    assert get_mullen_assessment(workspace.patient_id, first_id) == original_scores
    assert page.input_state() == draft
    assert workspace.has_unsaved_changes()
    assert page.assessment_id == (None if new_summary else first_id)
    with get_connection() as connection:
        connection.execute("DROP TRIGGER reject_pending")
    assert workspace.save_current_section()
    assert not workspace.has_unsaved_changes()
    assert len(list_mullen_assessments(workspace.patient_id)) == (2 if new_summary else 1)
    assert page.raw_score_inputs[0].text() == ""
