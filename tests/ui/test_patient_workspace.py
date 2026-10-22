from datetime import date

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from app.database.repositories.forms import (
    get_screening_questionnaire,
    get_telephone_screening,
)
from app.database.repositories.patients import (
    create_patient,
    get_patient,
    update_patient,
)
from app.database.repositories.videos import list_patient_videos
from app.services.preferences import DEFAULT_PREFERENCES
from app.ui.dialogs.patient_detail_view import PatientDetailView


@pytest.fixture
def workspace(temp_database, qtbot, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[-1]))
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel
    )
    patient_id = create_patient("WORKSPACE-1")
    view = PatientDetailView(patient_id)
    view.warnings = warnings
    qtbot.addWidget(view)
    view.show()
    return view


def test_overview_save_shares_identity_and_risk(workspace, qtbot):
    view = workspace
    overview = view.overview_view
    overview.child_name_input.setText("Avery Example")
    overview.date_of_birth_input.setText("2026-08-20")
    overview.sex_combo.setCurrentText("Female")
    overview.high_risk_checkbox.click()
    assert view.save_status.text() == "Unsaved changes"
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)
    assert not view.has_unsaved_changes()
    assert get_patient(view.patient_id)["risk"] == 1
    view.navigation.setCurrentRow(2)
    questionnaire = view.screening_questionnaire_view
    assert questionnaire.child_name_input.text() == "Avery Example"
    assert questionnaire.date_of_birth_input.text() == "2026-08-20"
    assert questionnaire.sex_combo.currentText() == "Female"
    questionnaire.child_name_input.setText("Updated Name")
    assert view.save_current_section()
    view.navigation.setCurrentRow(0)
    assert overview.child_name_input.text() == "Updated Name"
    view.navigation.setCurrentRow(1)
    assert view.telephone_screening_view.high_risk_checkbox.isChecked()
    view.telephone_screening_view.low_risk_checkbox.click()
    assert view.save_current_section()
    view.navigation.setCurrentRow(0)
    assert overview.low_risk_checkbox.isChecked()
    assert not overview.high_risk_checkbox.isChecked()


def test_navigation_cancel_then_discard_restores_inputs(workspace, monkeypatch):
    view = workspace
    view.overview_view.child_name_input.setText("Unsaved Name")
    view.navigation.setCurrentRow(1)
    assert view.navigation.currentRow() == 0
    assert view.pages.currentIndex() == 0
    assert view.overview_view.child_name_input.text() == "Unsaved Name"
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard
    )
    view.navigation.setCurrentRow(1)
    view.navigation.setCurrentRow(0)
    assert view.overview_view.child_name_input.text() == ""
    assert not view.has_unsaved_changes()
    assert get_patient(view.patient_id)["child_name"] is None


def test_navigation_save_loads_shared_data(workspace, monkeypatch):
    view = workspace
    view.overview_view.child_name_input.setText("Saved On Navigation")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    view.navigation.setCurrentRow(2)
    assert view.pages.currentIndex() == 2
    assert (
        view.screening_questionnaire_view.child_name_input.text()
        == "Saved On Navigation"
    )


@pytest.mark.parametrize("close_method", ["button", "escape", "window"])
def test_close_cancel_preserves_edits(workspace, qtbot, close_method):
    view = workspace
    view.overview_view.child_name_input.setText("Still Editing")
    if close_method == "button":
        qtbot.mouseClick(view.close_button, Qt.MouseButton.LeftButton)
    elif close_method == "escape":
        qtbot.keyClick(view, Qt.Key.Key_Escape)
    else:
        view.close()
    assert view.isVisible()
    assert view.has_unsaved_changes()
    assert view.overview_view.child_name_input.text() == "Still Editing"


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


def test_failed_save_keeps_navigation_and_edits(workspace, monkeypatch):
    view = workspace
    view.overview_view.date_of_birth_input.setText("2026-02-30")
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    view.navigation.setCurrentRow(2)
    assert view.pages.currentIndex() == 0
    assert view.navigation.currentRow() == 0
    assert view.has_unsaved_changes()
    assert view.warnings == ["Enter date of birth as YYYY-MM-DD."]
    assert get_patient(view.patient_id)["date_of_birth"] is None


def test_duplicate_subject_id_does_not_save_partial_overview(workspace):
    view = workspace
    create_patient("TAKEN")
    view.overview_view.subject_id_input.setText("TAKEN")
    view.overview_view.child_name_input.setText("Should Not Save")
    view.overview_view.low_risk_checkbox.click()
    assert not view.save_current_section()
    patient = get_patient(view.patient_id)
    assert patient["subject_id"] == "WORKSPACE-1"
    assert patient["child_name"] is None
    assert patient["risk"] is None
    assert get_telephone_screening(view.patient_id) is None
    assert view.has_unsaved_changes()


@pytest.mark.parametrize("index", range(1, 8))
def test_common_save_saves_every_section(workspace, qtbot, index, tmp_path):
    view = workspace
    view.navigation.setCurrentRow(index)
    page = view.views[index]
    if index == 1:
        page.screener_input.setText("Test Screener")
    elif index == 2:
        page.parent_name_input.setText("Test Parent")
    elif index == 3:
        page.general_health_input.setPlainText("Healthy")
    elif index == 4:
        page.parent_autism_checkbox.setChecked(True)
    elif index == 5:
        page.rows["Consents"]["room"].setText("Room 1")
    elif index == 6:
        update_patient(view.patient_id, {"date_of_birth": "2025-01-01"})
        page.use_overview_dob()
        page.assessment_date_input.setText("2025-03-01")
        page.confidence_combo.setCurrentIndex(page.confidence_combo.findData(90))
        page.age_calculation_combo.setCurrentIndex(page.age_calculation_combo.findData("calendar"))
        page.raw_score_inputs[0].setText("3")
    else:
        video = tmp_path / "video.mp4"
        video.write_bytes(b"test reference")
        page.file_path_input.setText(str(video))
        page.title_input.setText("Recording")
    assert view.has_unsaved_changes()
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)
    assert not view.warnings
    assert not view.has_unsaved_changes()
    if index == 7:
        videos = list_patient_videos(view.patient_id)
        assert len(videos) == 1
        assert videos[0]["file_path"] == str(video)
        assert page.table.rowCount() == 1
    else:
        saved_state = view._input_state(page)
        view.navigation.setCurrentRow(0)
        view.navigation.setCurrentRow(index)
        assert view._input_state(page) == saved_state


def test_invalid_mullen_input_remains_unsaved(workspace, monkeypatch):
    view = workspace
    view.navigation.setCurrentRow(6)
    view.views[6].raw_score_inputs[0].setText("invalid")
    assert not view.save_current_section()
    assert view.has_unsaved_changes()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Save
    )
    view.close()
    assert view.isVisible()


def test_eligibility_and_completion_refresh(workspace):
    view = workspace
    view.navigation.setCurrentRow(1)
    view.telephone_screening_view.eligibility_combo.setCurrentText("Yes")
    assert view.save_current_section()
    assert view.eligibility_label.text() == "Yes"
    assert view.mark_complete_button.isEnabled()
    view.mark_complete_button.click()
    assert get_patient(view.patient_id)["form_status"] == "Complete"
    assert view.form_status_label.text() == "Complete"
    view.mark_complete_button.click()
    assert get_patient(view.patient_id)["form_status"] == "Pending"


def test_new_patient_flow_opens_workspace(temp_database, qtbot, monkeypatch):
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
    assert opened[0].navigation.currentRow() == 0
    assert opened[0].overview_view.subject_id_input.text() == "NEW-PATIENT"
    assert opened[0].navigation.count() == 8


def test_questionnaire_copy_tracks_overview_updates(workspace):
    view = workspace
    view.navigation.setCurrentRow(2)
    view.screening_questionnaire_view.child_name_input.setText("Before")
    view.screening_questionnaire_view.parent_name_input.setText("Preserved Parent")
    assert view.save_current_section()
    view.navigation.setCurrentRow(0)
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


def test_disabled_unsaved_warning_discards_without_prompt(
    temp_database, qtbot, monkeypatch
):
    patient_id = create_patient("NO-WARNING")
    preferences = {**DEFAULT_PREFERENCES, "warn_unsaved_changes": False}
    view = PatientDetailView(patient_id, preferences=preferences)
    qtbot.addWidget(view)
    view.show()
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args: pytest.fail("No unsaved-change prompt was expected"),
    )

    view.overview_view.child_name_input.setText("Discard me")
    view.navigation.setCurrentRow(1)
    assert view.pages.currentIndex() == 1
    view.close()
    assert not view.isVisible()
    assert get_patient(patient_id)["child_name"] is None


def test_telephone_save_shows_automatic_ineligibility(workspace, qtbot):
    view = workspace
    update_patient(view.patient_id, {"date_of_birth": date.today().isoformat()})
    view.navigation.setCurrentRow(1)
    telephone = view.telephone_screening_view
    telephone.eligibility_combo.setCurrentText("Yes")
    telephone.gestational_input.setText("35")
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)

    assert telephone.eligibility_combo.currentText() == "No"
    assert telephone.eligibility_comment_input.text() == "Born at or before 37 weeks gestation."
    assert not telephone.eligibility_comment_input.isHidden()
    assert not view.has_unsaved_changes()
    assert view.eligibility_label.text() == "No"


def test_overview_birthday_shows_automatic_ineligibility_on_telephone_tab(workspace, qtbot):
    view = workspace
    view.overview_view.date_of_birth_input.setText("2007-09-27")
    qtbot.mouseClick(view.save_button, Qt.MouseButton.LeftButton)
    view.navigation.setCurrentRow(1)

    telephone = view.telephone_screening_view
    assert telephone.eligibility_combo.currentText() == "No"
    assert telephone.eligibility_comment_input.text() == "Age is 3 months or older."


def test_telephone_form_button_shows_automatic_ineligibility(temp_database, qtbot, monkeypatch):
    from app.ui.forms.telephone_screening_view import TelephoneScreeningView

    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    patient_id = create_patient("FORM-1")
    update_patient(patient_id, {"date_of_birth": date.today().isoformat()})
    form = TelephoneScreeningView(patient_id)
    qtbot.addWidget(form)
    form.eligibility_combo.setCurrentText("Yes")
    form.gestational_input.setText("35")

    assert form.save()
    assert form.eligibility_combo.currentText() == "No"
    assert form.eligibility_comment_input.text() == "Born at or before 37 weeks gestation."
