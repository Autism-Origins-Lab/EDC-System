import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QPushButton

from app.database.connection import get_connection
from app.database.repositories.forms import (
    get_mullen_assessment,
    get_screening_questionnaire,
    get_telephone_screening,
    save_medical_history,
    save_mullen_assessment,
    save_telephone_screening,
)
from app.database.repositories.patients import (
    complete_patient_form,
    create_patient,
    get_patient,
    update_patient,
)
from app.database.repositories.videos import list_patient_videos
from app.services.preferences import DEFAULT_PREFERENCES
from app.ui.dialogs.patient_detail_view import PatientDetailView


@pytest.fixture
def workspace(temp_database, qtbot, monkeypatch):
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: pytest.fail("Step saves should be inline"),
    )
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[-1]))
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel
    )
    patient_id = create_patient("WORKSPACE-1")
    view = PatientDetailView(patient_id, preferences=DEFAULT_PREFERENCES.copy())
    view.warnings = warnings
    qtbot.addWidget(view)
    view.show()
    return view


def advance_to_review(view):
    while view._current_index < view.review_index:
        assert view.save_and_continue(), view.warnings


def test_progress_is_read_only_and_save_advances_after_persisting(workspace, qtbot):
    view = workspace
    assert not view.back_button.isEnabled()
    assert view.save_button.text() == "Save and Continue"
    assert not view.progress.findChildren(QPushButton)
    qtbot.mouseClick(view.progress.steps[4], Qt.MouseButton.LeftButton)
    assert view.pages.currentIndex() == 0
    view.overview_view.child_name_input.setText("Avery Example")
    view.overview_view.date_of_birth_input.setText("2026-08-20")
    view.overview_view.high_risk_checkbox.click()
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)
    assert view.pages.currentIndex() == 1
    assert get_patient(view.patient_id)["child_name"] == "Avery Example"
    assert get_patient(view.patient_id)["risk"] == 1
    assert view.progress.steps[0].property("stepState") == "saved"
    assert view.progress.steps[1].property("stepState") == "current"
    assert view.progress.steps[2].property("stepState") == "upcoming"
    assert view.step_label.text() == "Step 2 of 9"
    assert not view.has_unsaved_changes()
    assert view.save_and_continue()
    assert view.screening_questionnaire_view.child_name_input.text() == "Avery Example"


def test_back_preserves_drafts_and_shared_fields_refresh(workspace):
    view = workspace
    save_telephone_screening(view.patient_id, {"screener": "Saved Screener"})
    assert view.save_and_continue()
    view.telephone_screening_view.birthweight_input.setText("3.2 kg")
    view.go_back()
    assert view.pages.currentIndex() == 0
    view.overview_view.child_name_input.setText("Updated Name")
    assert view.save_and_continue()
    assert view.telephone_screening_view.birthweight_input.text() == "3.2 kg"
    assert view.save_and_continue()
    assert view.screening_questionnaire_view.child_name_input.text() == "Updated Name"
    assert get_telephone_screening(view.patient_id)["birthweight"] == "3.2 kg"
    assert get_telephone_screening(view.patient_id)["screener"] == "Saved Screener"


def test_invalid_input_blocks_advancement(workspace):
    view = workspace
    view.overview_view.date_of_birth_input.setText("2026-02-30")
    assert not view.save_and_continue()
    assert view.pages.currentIndex() == 0
    assert view.progress.steps[1].property("stepState") == "upcoming"
    assert view.has_unsaved_changes()
    assert view.warnings == ["Enter date of birth as YYYY-MM-DD."]
    assert get_patient(view.patient_id)["date_of_birth"] is None


def test_back_keeps_questionnaire_draft_and_refreshes_saved_identity(workspace):
    view = workspace
    assert view.save_and_continue()
    assert view.save_and_continue()
    view.screening_questionnaire_view.parent_name_input.setText("Draft Parent")
    view.go_back()
    view.go_back()
    view.overview_view.child_name_input.setText("New shared name")
    assert view.save_and_continue()
    assert view.save_and_continue()
    assert view.screening_questionnaire_view.parent_name_input.text() == "Draft Parent"
    assert (
        view.screening_questionnaire_view.child_name_input.text() == "New shared name"
    )
    assert view.has_unsaved_changes()
    assert view.save_and_continue()
    assert get_patient(view.patient_id)["child_name"] == "New shared name"


def test_back_keeps_first_medical_draft_unsaved_until_continue(workspace):
    view = workspace
    while view._current_index < 3:
        assert view.save_and_continue()
    view.medical_history_view.general_health_input.setPlainText("Draft history")
    view.medical_history_view.seen_neurologist_input.set_value(0)
    view.go_back()
    assert view.save_and_continue()
    assert (
        view.medical_history_view.general_health_input.toPlainText() == "Draft history"
    )
    assert view.medical_history_view.seen_neurologist_input.value() == 0
    assert view.has_unsaved_changes()


def test_duplicate_subject_id_does_not_save_partial_overview(workspace):
    view = workspace
    create_patient("TAKEN")
    view.overview_view.subject_id_input.setText("TAKEN")
    view.overview_view.child_name_input.setText("Should Not Save")
    view.overview_view.low_risk_checkbox.click()
    assert not view.save_and_continue()
    patient = get_patient(view.patient_id)
    assert patient["subject_id"] == "WORKSPACE-1"
    assert patient["child_name"] is None
    assert patient["risk"] is None
    assert get_telephone_screening(view.patient_id) is None


@pytest.mark.parametrize("index", range(1, 8))
def test_save_and_continue_saves_each_section(workspace, index, tmp_path):
    view = workspace
    view._show_step(index)
    page = view.views[index]
    if index == 1:
        page.birthweight_input.setText("3.2 kg")
    elif index == 2:
        page.parent_name_input.setText("Test Parent")
    elif index == 3:
        page.general_health_input.setPlainText("Healthy")
    elif index == 4:
        page.parent_autism_input.set_value(1)
    elif index == 5:
        page.rows["Consents"]["room"].setText("Room 1")
    elif index == 6:
        update_patient(view.patient_id, {"date_of_birth": "2025-01-01"})
        page.use_overview_dob()
        page.assessment_date_input.setText("2025-03-01")
        page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(90))
        page.age_calculation_combo.setCurrentIndex(
            page.age_calculation_combo.findData("calendar")
        )
        page.raw_score_inputs[0].setText("0")
    else:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"test reference")
        page.file_path_input.setText(str(video))
        page.title_input.setText("Recording")
    assert view.save_and_continue()
    assert view.pages.currentIndex() == index + 1
    assert not view.has_unsaved_changes()
    view.go_back()
    if index == 7:
        videos = list_patient_videos(view.patient_id)
        assert len(videos) == 1
        assert videos[0]["file_path"] == str(video)
        assert page.table.rowCount() == 1
        assert view.save_and_continue()
        assert len(list_patient_videos(view.patient_id)) == 1
    else:
        assert view._input_state(page) == view._saved_states[index]


def test_empty_optional_sections_reach_summary_without_inventing_values(workspace):
    view = workspace
    advance_to_review(view)
    assert view.save_button.text() == "Mark as Complete"
    assert not view.save_button.isEnabled()
    assert get_mullen_assessment(view.patient_id) == {}
    assert list_patient_videos(view.patient_id) == []
    answers = dict(view.summary_view.answers)
    assert dict(answers["Patient overview"])["Participant / Child name"] == "N/A"
    assert dict(answers["Mullen assessment"])["Gross Motor / Raw score"] == "N/A"
    assert dict(answers["Video references"])["Video references"] == "N/A"
    assert dict(answers["Medical history"])["Seen neurologist"] == "N/A"
    assert dict(answers["Family medical history"])["Child has siblings"] == "N/A"
    assert (
        dict(answers["Screening questionnaire"])["Mother listed is biological mother"]
        == "N/A"
    )
    assert dict(answers["Telephone screening"])["High familial risk"] == "N/A"
    assert dict(answers["Telephone screening"])["Low familial risk"] == "N/A"
    assert get_patient(view.patient_id)["child_name"] == ""
    assert get_patient(view.patient_id)["form_status"] == "Pending"
    assert not view.complete_form()


def test_summary_contains_answers_and_preserves_zero_and_no(workspace):
    view = workspace
    view.overview_view.child_name_input.setText("Avery <Example>")
    view.overview_view.date_of_birth_input.setText("2025-01-01")
    assert view.save_and_continue()
    save_telephone_screening(view.patient_id, {"screener": "Jordan Staff"})
    while view._current_index < 3:
        assert view.save_and_continue()
    view.medical_history_view.seen_neurologist_input.set_value(0)
    while view._current_index < 6:
        assert view.save_and_continue()
    mullen = view.mullen_view
    mullen.assessment_date_input.setText("2025-03-01")
    mullen.confidence_combo.setCurrentIndex(mullen.confidence_combo.findData(90))
    mullen.age_calculation_combo.setCurrentIndex(
        mullen.age_calculation_combo.findData("calendar")
    )
    mullen.raw_score_inputs[0].setText("0")
    advance_to_review(view)
    answers = dict(view.summary_view.answers)
    assert (
        dict(answers["Patient overview"])["Participant / Child name"]
        == "Avery <Example>"
    )
    assert dict(answers["Mullen assessment"])["Gross Motor / Raw score"] == "0"
    assert dict(answers["Medical history"])["Seen neurologist"] == "No"
    assert view.summary_view.screener_input.text() == "Jordan Staff"
    assert view.save_button.isEnabled()


@pytest.mark.parametrize("eligibility", ["Yes", "No", "Not evaluated"])
def test_final_completion_requires_screener_but_not_eligibility(
    workspace, qtbot, eligibility
):
    view = workspace
    assert view.save_and_continue()
    view.telephone_screening_view.eligibility_combo.setCurrentText(eligibility)
    advance_to_review(view)
    assert not view.save_button.isEnabled()
    view.summary_view.screener_input.setText("   ")
    assert not view.save_button.isEnabled()
    view.summary_view.screener_input.setText("  Jordan Staff  ")
    assert view.save_button.isEnabled()
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)
    assert view.result() == view.DialogCode.Accepted
    assert get_patient(view.patient_id)["form_status"] == "Complete"
    screening = get_telephone_screening(view.patient_id)
    assert screening["screener"] == "Jordan Staff"
    assert screening["eligibility"] == eligibility


def test_completion_cannot_be_triggered_before_review(workspace):
    view = workspace
    view.summary_view.screener_input.setText("Jordan Staff")
    assert not view.complete_form()
    view._show_step(view.review_index)
    assert not view.complete_form()
    assert get_patient(view.patient_id)["form_status"] == "Pending"


def test_editing_completed_record_requires_review_again(workspace):
    view = workspace
    complete_patient_form(view.patient_id, "Jordan Staff")
    view.refresh_data()
    view.overview_view.child_name_input.setText("Corrected name")
    assert view.save_and_continue()
    assert get_patient(view.patient_id)["form_status"] == "Pending"
    advance_to_review(view)
    assert view.complete_form()
    assert get_patient(view.patient_id)["form_status"] == "Complete"


def test_failed_status_reset_rolls_back_edited_answers(workspace):
    view = workspace
    update_patient(view.patient_id, {"child_name": "Original name"})
    complete_patient_form(view.patient_id, "Jordan Staff")
    view._show_step(0)
    view.refresh_data()
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_pending BEFORE UPDATE OF form_status ON patients "
            "WHEN NEW.form_status = 'Pending' "
            "BEGIN SELECT RAISE(ABORT, 'simulated status failure'); END"
        )

    view.overview_view.child_name_input.setText("Corrected name")
    assert not view.save_and_continue()
    patient = get_patient(view.patient_id)
    assert patient["child_name"] == "Original name"
    assert patient["form_status"] == "Complete"
    assert view.overview_view.child_name_input.text() == "Corrected name"
    assert view.has_unsaved_changes()
    assert view.pages.currentIndex() == 0
    assert view.warnings == ["simulated status failure"]

    with get_connection() as connection:
        connection.execute("DROP TRIGGER reject_pending")
    assert view.save_and_continue()
    patient = get_patient(view.patient_id)
    assert patient["child_name"] == "Corrected name"
    assert patient["form_status"] == "Pending"


@pytest.mark.parametrize("index", range(1, 9))
def test_status_failure_rolls_back_every_section_and_allows_retry(
    workspace, index, tmp_path,
):
    view = workspace
    update_patient(view.patient_id, {"date_of_birth": "2025-01-01"})
    advance_to_review(view)
    save_mullen_assessment(
        view.patient_id,
        {"gross_motor": {"raw_score": 0}},
        context={
            "assessment_date": "2025-03-01",
            "scoring_date_of_birth": "2025-01-01",
            "confidence_level": 90,
            "age_calculation": "calendar",
        },
    )
    complete_patient_form(view.patient_id, "Original Screener")
    view._show_step(index)
    view.refresh_data()
    page = view.views[index]
    if index == 1:
        page.birthweight_input.setText("3.2 kg")
        page.high_risk_checkbox.setChecked(True)
    elif index == 2:
        page.child_name_input.setText("Changed shared name")
        page.parent_name_input.setText("Changed parent")
    elif index == 3:
        page.general_health_input.setPlainText("Changed health")
        page.seen_neurologist_input.set_value(0)
    elif index == 4:
        page.parent_autism_input.set_value(1)
    elif index == 5:
        for procedure, fields in page.rows.items():
            fields["room"].setText(f"Changed {procedure} room")
    elif index == 6:
        page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(95))
        page.raw_score_inputs[0].setText("1")
    elif index == 7:
        page.file_path_input.setText(str(tmp_path / "recording.mp4"))
        page.title_input.setText("New recording")
    else:
        page.screener_input.setText("Changed Screener")

    tables = (
        "patients",
        "telephone_screenings",
        "screening_questionnaires",
        "medical_histories",
        "family_medical_histories",
        "procedure_schedules",
        "mullen_assessments",
        "mullen_scores",
        "patients_video",
    )

    def snapshot():
        with get_connection() as connection:
            return {
                table: [
                    tuple(row)
                    for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")
                ]
                for table in tables
            }

    original = snapshot()
    draft = view._input_state(page)
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_pending BEFORE UPDATE OF form_status ON patients "
            "WHEN NEW.form_status = 'Pending' "
            "BEGIN SELECT RAISE(ABORT, 'simulated status failure'); END"
        )
    # Review edits use this path when saving before closing the workspace.
    save = (
        view.save_current_section
        if index == view.review_index
        else view.save_and_continue
    )
    assert not save()
    assert snapshot() == original
    assert view.is_complete()
    assert view._input_state(page) == draft
    assert view.has_unsaved_changes()
    assert view.pages.currentIndex() == index
    assert view.warnings == ["simulated status failure"]
    if index == 7:
        assert page.table.rowCount() == 0

    with get_connection() as connection:
        connection.execute("DROP TRIGGER reject_pending")
    assert save()
    assert get_patient(view.patient_id)["form_status"] == "Pending"
    assert not view.has_unsaved_changes()
    if index == 7:
        assert len(list_patient_videos(view.patient_id)) == 1
        assert page.table.rowCount() == 1


def test_save_uses_current_database_completion_status(workspace):
    view = workspace
    assert not view.is_complete()
    complete_patient_form(view.patient_id, "Jordan Staff")
    view.overview_view.child_name_input.setText("Edited since completion")
    assert view.save_and_continue()
    assert get_patient(view.patient_id)["form_status"] == "Pending"


def test_unchanged_save_preserves_completion(workspace):
    view = workspace
    complete_patient_form(view.patient_id, "Jordan Staff")
    view._show_step(0)
    view.refresh_data()
    assert view.save_and_continue()
    assert get_patient(view.patient_id)["form_status"] == "Complete"


def test_unsuccessful_section_save_discards_any_writes(workspace, monkeypatch):
    view = workspace
    complete_patient_form(view.patient_id, "Jordan Staff")
    view._show_step(3)
    view.refresh_data()
    view.medical_history_view.general_health_input.setPlainText("Keep draft")

    def rejected_save(**kwargs):
        save_medical_history(view.patient_id, {"general_health": "Must roll back"})
        return False

    monkeypatch.setattr(view.medical_history_view, "save", rejected_save)
    assert not view.save_and_continue()
    assert get_patient(view.patient_id)["form_status"] == "Complete"
    with get_connection() as connection:
        assert connection.execute("SELECT * FROM medical_histories").fetchall() == []
    assert view.medical_history_view.general_health_input.toPlainText() == "Keep draft"
    assert view.has_unsaved_changes()
    assert view.pages.currentIndex() == 3


@pytest.mark.parametrize("index", [0, 8])
def test_close_save_failure_keeps_completed_record_and_dialog_open(
    workspace, monkeypatch, index,
):
    view = workspace
    complete_patient_form(view.patient_id, "Original Screener")
    view._show_step(index)
    view.refresh_data()
    field = (
        view.overview_view.child_name_input
        if index == 0
        else view.summary_view.screener_input
    )
    field.setText("Keep draft")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_pending BEFORE UPDATE OF form_status ON patients "
            "WHEN NEW.form_status = 'Pending' "
            "BEGIN SELECT RAISE(ABORT, 'simulated status failure'); END"
        )
    view.close()
    assert view.isVisible()
    assert field.text() == "Keep draft"
    assert view.has_unsaved_changes()
    patient = get_patient(view.patient_id)
    assert patient["child_name"] is None
    assert patient["form_status"] == "Complete"
    assert get_telephone_screening(view.patient_id)["screener"] == "Original Screener"
    assert view.warnings == ["simulated status failure"]


def test_database_failure_keeps_edits_and_current_step(workspace):
    view = workspace
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_overview BEFORE UPDATE ON patients "
            "BEGIN SELECT RAISE(ABORT, 'simulated save failure'); END"
        )
    view.overview_view.child_name_input.setText("Keep these edits")
    assert not view.save_and_continue()
    assert view.pages.currentIndex() == 0
    assert view.overview_view.child_name_input.text() == "Keep these edits"
    assert view.warnings == ["simulated save failure"]


@pytest.mark.parametrize("close_method", ["escape", "window"])
def test_close_cancel_preserves_edits(workspace, qtbot, close_method):
    view = workspace
    view.overview_view.child_name_input.setText("Still Editing")
    if close_method == "escape":
        qtbot.keyClick(view, Qt.Key.Key_Escape)
    else:
        view.close()
    assert view.isVisible()
    assert view.has_unsaved_changes()


@pytest.mark.parametrize(
    "choice", [QMessageBox.StandardButton.Save, QMessageBox.StandardButton.Discard]
)
def test_close_save_or_discard(workspace, monkeypatch, choice):
    view = workspace
    view.overview_view.child_name_input.setText("Closing Name")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: choice)
    view.close()
    assert not view.isVisible()
    expected = "Closing Name" if choice == QMessageBox.StandardButton.Save else None
    assert get_patient(view.patient_id)["child_name"] == expected


def test_close_saves_drafts_retained_on_previous_steps(workspace, monkeypatch):
    view = workspace
    assert view.save_and_continue()
    view.telephone_screening_view.birthweight_input.setText("3.2 kg")
    view.go_back()
    view.overview_view.child_name_input.setText("Draft Participant")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    view.close()
    assert not view.isVisible()
    assert get_patient(view.patient_id)["child_name"] == "Draft Participant"
    assert get_telephone_screening(view.patient_id)["birthweight"] == "3.2 kg"
    assert get_patient(view.patient_id)["form_status"] == "Pending"


def test_new_patient_flow_opens_first_step(temp_database, qtbot, monkeypatch):
    from app.ui.dialogs.new_patient_dialog import NewPatientDialog
    from app.ui.pages.patients_view import PatientsView

    def create_in_dialog(dialog):
        dialog.subject_id_input.setText("NEW-PATIENT")
        dialog.create_patient()
        return dialog.result()

    opened = []
    monkeypatch.setattr(NewPatientDialog, "exec", create_in_dialog)
    monkeypatch.setattr(PatientDetailView, "exec", lambda dialog: opened.append(dialog))
    patients = PatientsView()
    qtbot.addWidget(patients)
    patients.open_new_patient_dialog()
    assert len(opened) == 1
    qtbot.addWidget(opened[0])
    assert opened[0].pages.currentIndex() == 0
    assert len(opened[0].progress.steps) == 9
    assert opened[0].overview_view.subject_id_input.text() == "NEW-PATIENT"


def test_questionnaire_copy_tracks_overview_updates(workspace):
    view = workspace
    view._show_step(2)
    view.screening_questionnaire_view.child_name_input.setText("Before")
    view.screening_questionnaire_view.parent_name_input.setText("Preserved Parent")
    assert view.save_current_section()
    view._show_step(0)
    view.overview_view.child_name_input.setText("After")
    assert view.save_current_section()
    data = get_screening_questionnaire(view.patient_id)
    assert data["child_name"] == "After"
    assert data["parent_name"] == "Preserved Parent"


def test_delete_patient_respects_confirmation(workspace, monkeypatch):
    view = workspace
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    view.delete_current_patient()
    assert get_patient(view.patient_id) is None
    assert view.result() == view.DialogCode.Accepted


def test_disabled_unsaved_warning_closes_without_prompt(
    temp_database, qtbot, monkeypatch
):
    patient_id = create_patient("NO-WARNING")
    preferences = {**DEFAULT_PREFERENCES, "warn_unsaved_changes": False}
    view = PatientDetailView(patient_id, preferences=preferences)
    qtbot.addWidget(view)
    view.show()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: pytest.fail("No prompt expected")
    )
    view.overview_view.child_name_input.setText("Discard me")
    view.close()
    assert not view.isVisible()
    assert get_patient(patient_id)["child_name"] is None
