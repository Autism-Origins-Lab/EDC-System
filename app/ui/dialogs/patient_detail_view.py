from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.patients import (
    delete_patient,
    get_patient,
    update_patient_form,
)
from app.services.preferences import load_preferences
from app.ui.forms.family_medical_history_view import FamilyMedicalHistoryView
from app.ui.forms.medical_history_view import MedicalHistoryView
from app.ui.forms.mullen_view import MullenView
from app.ui.forms.patient_overview_view import PatientOverviewView
from app.ui.forms.procedure_schedule_view import ProcedureScheduleView
from app.ui.forms.screening_questionnaire_view import ScreeningQuestionnaireView
from app.ui.forms.telephone_screening_view import TelephoneScreeningView
from app.ui.forms.video_references_view import VideoReferencesView
from app.ui.theme import (
    DARK_PATIENT_WORKSPACE_STYLESHEET,
    PATIENT_DETAIL_COMPLETION_DISABLED_STYLESHEET,
    PATIENT_DETAIL_MARK_COMPLETE_STYLESHEET,
    PATIENT_DETAIL_UNMARK_COMPLETE_STYLESHEET,
    PATIENT_WORKSPACE_STYLESHEET,
    themed_stylesheet,
)

SECTION_DETAILS = (
    (
        "Overview",
        "Patient overview",
        "Participant identity and familial risk are shared across forms.",
    ),
    (
        "Telephone screening",
        "Telephone screening",
        "Record screening details, eligibility, and verbal consent.",
    ),
    (
        "Screening questionnaire",
        "Screening questionnaire",
        "Record participant and family contact information.",
    ),
    (
        "Medical history",
        "Medical history",
        "Record the participant's medical and developmental history.",
    ),
    (
        "Family medical history",
        "Family medical history",
        "Record relevant family diagnoses and sibling history.",
    ),
    (
        "Procedure schedule",
        "Procedure schedule",
        "Coordinate study procedures, staff, times, and rooms.",
    ),
    (
        "Mullen assessment",
        "Mullen assessment",
        "Enter developmental assessment scores for each scale.",
    ),
    (
        "Video references",
        "Video references",
        "Save references to local video files. Files stay in their original locations.",
    ),
)


class PatientDetailView(QDialog):
    patient_deleted = Signal(int)

    def __init__(self, patient_id: int, parent=None, preferences: dict | None = None):
        super().__init__(parent)
        self.preferences = preferences or load_preferences()
        self.patient_id = patient_id
        self.patient = get_patient(patient_id) or {}
        self._current_index = 0
        self._changing_page = False
        self._tracking_enabled = False
        self._saved_states: dict[int, tuple] = {}

        subject_id = self.patient.get("subject_id") or str(patient_id)
        self.setObjectName("PatientWorkspace")
        self.setWindowTitle(f"Patient {subject_id}")
        self.setMinimumSize(820, 600)
        self.resize(1200, 800)
        self.setStyleSheet(
            themed_stylesheet(
                PATIENT_WORKSPACE_STYLESHEET,
                DARK_PATIENT_WORKSPACE_STYLESHEET,
                self.preferences["theme"],
            )
        )

        self.overview_view = PatientOverviewView(patient_id)
        self.telephone_screening_view = TelephoneScreeningView(patient_id)
        self.screening_questionnaire_view = ScreeningQuestionnaireView(patient_id)
        self.medical_history_view = MedicalHistoryView(patient_id)
        self.family_medical_history_view = FamilyMedicalHistoryView(patient_id)
        self.procedure_schedule_view = ProcedureScheduleView(patient_id)
        self.mullen_view = MullenView(patient_id)
        self.video_references_view = VideoReferencesView(patient_id)
        self.views = [
            self.overview_view,
            self.telephone_screening_view,
            self.screening_questionnaire_view,
            self.medical_history_view,
            self.family_medical_history_view,
            self.procedure_schedule_view,
            self.mullen_view,
            self.video_references_view,
        ]

        self._hide_embedded_save_controls()
        self._build_layout()
        self.telephone_screening_view.screening_saved.connect(self.refresh_data)

        for index, view in enumerate(self.views):
            self._saved_states[index] = self._input_state(view)
            self._connect_input_tracking(view)

        self._tracking_enabled = True
        self.navigation.setCurrentRow(0)
        self.pages.setCurrentIndex(0)
        self._update_section_header(0)
        self.refresh_data()
        self._update_save_status()

    def _build_layout(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 16, 12, 10)
        root.setSpacing(30)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(18)

        self.navigation = QListWidget()
        self.navigation.setObjectName("PatientNavigation")
        self.navigation.setFixedWidth(230)
        self.navigation.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        for navigation_label, _title, _subtitle in SECTION_DETAILS:
            self.navigation.addItem(navigation_label)
        sidebar.addWidget(self.navigation, 1)

        local_note = QLabel("Changes are stored locally on this computer.")
        local_note.setObjectName("WorkspaceMuted")
        local_note.setWordWrap(True)
        local_note.setFixedWidth(230)
        sidebar.addWidget(local_note)
        root.addLayout(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(0, 10, 4, 0)
        content.setSpacing(10)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(20)
        self.section_title = QLabel()
        self.section_title.setObjectName("WorkspaceTitle")
        heading_row.addWidget(self.section_title)
        heading_row.addStretch()

        self.mark_complete_button = QPushButton()
        self.mark_complete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mark_complete_button.clicked.connect(self.mark_or_unmark_completion)
        heading_row.addWidget(self.mark_complete_button)
        content.addLayout(heading_row)

        self.section_subtitle = QLabel()
        self.section_subtitle.setObjectName("WorkspaceMuted")
        self.section_subtitle.setWordWrap(True)
        content.addWidget(self.section_subtitle)

        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        status_row.addWidget(QLabel("Eligibility:")) 
        self.eligibility_label = QLabel()
        status_row.addWidget(self.eligibility_label)
        status_row.addSpacing(24)
        status_row.addWidget(QLabel("Form status:"))
        self.form_status_label = QLabel()
        status_row.addWidget(self.form_status_label)
        status_row.addStretch()
        content.addLayout(status_row)

        self.pages = QStackedWidget()
        for view in self.views:
            self.pages.addWidget(self._scrollable_page(view))
        content.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        footer.setSpacing(20)
        self.save_status = QLabel("All changes saved")
        self.save_status.setObjectName("WorkspaceMuted")
        footer.addWidget(self.save_status, 1, Qt.AlignmentFlag.AlignBottom)

        self.delete_button = QPushButton("Delete patient")
        self.delete_button.setObjectName("WorkspaceDelete")
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(self.delete_current_patient)
        footer.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignBottom)

        actions = QVBoxLayout()
        actions.setSpacing(16)
        self.save_button = QPushButton("Save changes")
        self.save_button.setObjectName("WorkspaceSave")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_current_section)
        actions.addWidget(self.save_button)

        self.close_button = QPushButton("Close workspace")
        self.close_button.setObjectName("WorkspaceClose")
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.close)
        actions.addWidget(self.close_button)
        footer.addLayout(actions)
        content.addLayout(footer)

        root.addLayout(content, 1)
        self.navigation.currentRowChanged.connect(self._navigate_to)

    @staticmethod
    def _scrollable_page(view: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(view)
        return scroll_area

    def _hide_embedded_save_controls(self) -> None:
        for view in self.views:
            for button in view.findChildren(QPushButton):
                if button.objectName() == "PrimaryButton":
                    button.hide()

        for label in self.mullen_view.findChildren(QLabel):
            if label.objectName() in {"PageTitle", "Muted"}:
                label.hide()

    def _connect_input_tracking(self, view: QWidget) -> None:
        for field in view.findChildren(QLineEdit):
            field.textChanged.connect(self._mark_unsaved)
        for field in view.findChildren(QTextEdit):
            field.textChanged.connect(self._mark_unsaved)
        for field in view.findChildren(QComboBox):
            field.currentIndexChanged.connect(self._mark_unsaved)
        for field in view.findChildren(QCheckBox):
            field.toggled.connect(self._mark_unsaved)

    @staticmethod
    def _input_widgets(view: QWidget) -> list[QWidget]:
        return [
            *view.findChildren(QLineEdit),
            *view.findChildren(QTextEdit),
            *view.findChildren(QComboBox),
            *view.findChildren(QCheckBox),
        ]

    def _input_state(self, view: QWidget) -> tuple:
        state = []
        for field in self._input_widgets(view):
            if isinstance(field, QLineEdit):
                state.append(("line", field.text()))
            elif isinstance(field, QTextEdit):
                state.append(("text", field.toPlainText()))
            elif isinstance(field, QComboBox):
                state.append(("combo", field.currentText()))
            elif isinstance(field, QCheckBox):
                state.append(("check", field.isChecked()))
        return tuple(state)

    def _restore_input_state(self, view: QWidget, state: tuple) -> None:
        self._tracking_enabled = False
        try:
            for field, (_kind, value) in zip(self._input_widgets(view), state):
                if isinstance(field, QLineEdit):
                    field.setText(value)
                elif isinstance(field, QTextEdit):
                    field.setPlainText(value)
                elif isinstance(field, QComboBox):
                    field.setCurrentText(value)
                elif isinstance(field, QCheckBox):
                    field.setChecked(value)
        finally:
            self._tracking_enabled = True
        self._update_save_status()

    def _reload_view(self, index: int) -> None:
        view = self.views[index]
        loader = getattr(view, "load_existing_data", None)
        if not callable(loader):
            return

        self._tracking_enabled = False
        try:
            loader()
        finally:
            self._tracking_enabled = True
        self._saved_states[index] = self._input_state(view)

    def _mark_unsaved(self, *_args) -> None:
        if self._tracking_enabled:
            self._update_save_status()

    def has_unsaved_changes(self) -> bool:
        return any(
            self._input_state(view) != self._saved_states.get(index, ())
            for index, view in enumerate(self.views)
        )

    def _update_save_status(self) -> None:
        self.save_status.setText(
            "Unsaved changes" if self.has_unsaved_changes() else "All changes saved"
        )

    def _update_section_header(self, index: int) -> None:
        _navigation_label, title, subtitle = SECTION_DETAILS[index]
        self.section_title.setText(title)
        self.section_subtitle.setText(subtitle)

    def _navigate_to(self, target_index: int) -> None:
        if self._changing_page or target_index < 0 or target_index == self._current_index:
            return

        current_view = self.views[self._current_index]
        if self._input_state(current_view) != self._saved_states[self._current_index]:
            if not self.preferences["warn_unsaved_changes"]:
                self._restore_input_state(
                    current_view, self._saved_states[self._current_index]
                )
            else:
                if not self._resolve_unsaved_navigation(current_view):
                    return

        self._reload_view(target_index)
        self._current_index = target_index
        self.pages.setCurrentIndex(target_index)
        self._update_section_header(target_index)
        self._update_save_status()

    def _resolve_unsaved_navigation(self, current_view: QWidget) -> bool:
        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            "Save changes before leaving this section?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            self._reset_navigation_selection()
            return False
        if choice == QMessageBox.StandardButton.Save:
            if not self.save_current_section():
                self._reset_navigation_selection()
                return False
        else:
            self._restore_input_state(
                current_view, self._saved_states[self._current_index]
            )
        return True

    def _reset_navigation_selection(self) -> None:
        self._changing_page = True
        try:
            self.navigation.setCurrentRow(self._current_index)
        finally:
            self._changing_page = False

    def save_current_section(self) -> bool:
        view = self.views[self._current_index]
        saver = getattr(view, "save", None)
        if not callable(saver):
            return True

        try:
            saved = saver()
        except ValueError as exc:
            QMessageBox.warning(self, "Unable to save", str(exc))
            self._update_save_status()
            return False

        if saved is False:
            self._update_save_status()
            return False

        self._reload_view(self._current_index)
        self.refresh_data()
        self._update_save_status()
        return True

    def mark_or_unmark_completion(self) -> None:
        self.patient = get_patient(self.patient_id) or {}
        if not self.is_eligible():
            self.refresh_button_state()
            return

        new_status = "Pending" if self.is_complete() else "Complete"
        update_patient_form(self.patient_id, new_status)
        self.refresh_data()

    def refresh_button_state(self) -> None:
        if not self.is_eligible():
            self.mark_complete_button.setEnabled(False)
            self.mark_complete_button.setStyleSheet(
                PATIENT_DETAIL_COMPLETION_DISABLED_STYLESHEET
            )
            self.mark_complete_button.setText("Must Be Eligible to Mark Complete")
        elif self.is_complete():
            self.mark_complete_button.setEnabled(True)
            self.mark_complete_button.setStyleSheet(
                PATIENT_DETAIL_UNMARK_COMPLETE_STYLESHEET
            )
            self.mark_complete_button.setText("Unmark Complete")
        else:
            self.mark_complete_button.setEnabled(True)
            self.mark_complete_button.setStyleSheet(
                PATIENT_DETAIL_MARK_COMPLETE_STYLESHEET
            )
            self.mark_complete_button.setText("Mark Complete")

    def is_eligible(self) -> bool:
        return self.patient.get("eligibility") == "Yes"

    def is_complete(self) -> bool:
        return self.patient.get("form_status") == "Complete"

    def refresh_data(self, *_args) -> None:
        self.patient = get_patient(self.patient_id) or {}
        subject_id = self.patient.get("subject_id") or str(self.patient_id)
        self.setWindowTitle(f"Patient {subject_id}")
        self.eligibility_label.setText(
            self.patient.get("eligibility") or "Not Evaluated"
        )
        self.form_status_label.setText(self.patient.get("form_status") or "Pending")
        self.refresh_button_state()

    def _confirm_close(self) -> bool:
        if (
            not self.has_unsaved_changes()
            or not self.preferences["warn_unsaved_changes"]
        ):
            return True

        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            "Save changes before closing this workspace?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        if choice == QMessageBox.StandardButton.Save:
            return self.save_current_section()
        return True

    def delete_current_patient(self) -> None:
        subject_id = self.patient.get("subject_id") or str(self.patient_id)
        if self.preferences["confirm_delete"]:
            choice = QMessageBox.question(
                self,
                "Delete patient",
                f"Permanently delete patient {subject_id} and all related records?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
        delete_patient(self.patient_id)
        self.patient_deleted.emit(self.patient_id)
        self.accept()

    def reject(self) -> None:
        if self._confirm_close():
            super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_close():
            event.accept()
        else:
            event.ignore()
