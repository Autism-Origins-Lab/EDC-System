import sqlite3

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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.patients import (
    complete_patient_form,
    delete_patient,
    get_patient,
    update_patient_form,
)
from app.services.preferences import load_preferences
from app.ui.forms.family_medical_history_view import FamilyMedicalHistoryView
from app.ui.forms.medical_history_view import MedicalHistoryView
from app.ui.forms.mullen_view import MullenView
from app.ui.forms.patient_overview_view import PatientOverviewView
from app.ui.forms.patient_summary_view import PatientSummaryView
from app.ui.forms.procedure_schedule_view import ProcedureScheduleView
from app.ui.forms.screening_questionnaire_view import ScreeningQuestionnaireView
from app.ui.forms.telephone_screening_view import TelephoneScreeningView
from app.ui.forms.video_references_view import VideoReferencesView
from app.ui.theme import (
    DARK_PATIENT_WORKSPACE_STYLESHEET,
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
    (
        "Review",
        "Review answers",
        "Check the saved answers and record the screener before completing the form.",
    ),
)

STEP_LABELS = (
    "Overview",
    "Screening",
    "Questionnaire",
    "Medical history",
    "Family history",
    "Procedures",
    "Mullen",
    "Videos",
    "Review",
)


class FormProgress(QWidget):
    """A read-only section indicator; navigation happens through the footer."""

    def __init__(self):
        super().__init__()
        self.setObjectName("FormProgress")
        self.setAccessibleName("Form section progress")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.steps = []
        self.connectors = []
        for index, title in enumerate(STEP_LABELS):
            step = QFrame()
            step.setObjectName("FormStep")
            content = QVBoxLayout(step)
            content.setContentsMargins(0, 8, 0, 0)
            content.setSpacing(10)
            track = QWidget()
            track.setObjectName("FormStepTrack")
            track_layout = QHBoxLayout(track)
            track_layout.setContentsMargins(0, 0, 0, 0)
            track_layout.setSpacing(0)
            left = QFrame()
            left.setObjectName("FormConnector")
            left.setFixedHeight(3)
            left.setProperty("edge", index == 0)
            number = QLabel(str(index + 1))
            number.setObjectName("FormStepNumber")
            number.setFixedSize(44, 44)
            number.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right = QFrame()
            right.setObjectName("FormConnector")
            right.setFixedHeight(3)
            right.setProperty("edge", index == len(STEP_LABELS) - 1)
            track_layout.addWidget(left, 1)
            track_layout.addWidget(number)
            track_layout.addWidget(right, 1)
            content.addWidget(track)
            label = QLabel(title)
            label.setObjectName("FormStepTitle")
            label.setWordWrap(True)
            label.setMinimumHeight(36)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content.addWidget(label)
            layout.addWidget(step, 1)
            self.steps.append(step)
            self.connectors.append((left, right))

    def set_current_step(self, current):
        for index, step in enumerate(self.steps):
            state = (
                "saved"
                if index < current
                else "current"
                if index == current
                else "upcoming"
            )
            step.setProperty("stepState", state)
            left, right = self.connectors[index]
            left.setProperty("filled", index <= current)
            right.setProperty("filled", index < current)
            step.setAccessibleName(f"Step {index + 1}: {STEP_LABELS[index]}, {state}")
            for widget in [step, *step.findChildren(QWidget)]:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
        self.setAccessibleDescription(
            f"Step {current + 1} of {len(self.steps)}: {STEP_LABELS[current]}"
        )


class PatientDetailView(QDialog):
    patient_deleted = Signal(int)

    def __init__(self, patient_id: int, parent=None, preferences: dict | None = None):
        super().__init__(parent)
        self.preferences = preferences or load_preferences()
        self.patient_id = patient_id
        self.patient = get_patient(patient_id) or {}
        self._current_index = 0
        self._completed_steps = set()
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

        self.overview_view = PatientOverviewView(patient_id, self.preferences)
        self.telephone_screening_view = TelephoneScreeningView(
            patient_id, self.preferences
        )
        self.screening_questionnaire_view = ScreeningQuestionnaireView(
            patient_id, self.preferences
        )
        self.medical_history_view = MedicalHistoryView(patient_id)
        self.family_medical_history_view = FamilyMedicalHistoryView(patient_id)
        self.procedure_schedule_view = ProcedureScheduleView(patient_id)
        self.mullen_view = MullenView(patient_id, self.preferences)
        self.video_references_view = VideoReferencesView(patient_id)
        form_views = [
            self.overview_view,
            self.telephone_screening_view,
            self.screening_questionnaire_view,
            self.medical_history_view,
            self.family_medical_history_view,
            self.procedure_schedule_view,
            self.mullen_view,
            self.video_references_view,
        ]
        self.summary_view = PatientSummaryView(
            patient_id,
            form_views,
            [section[1] for section in SECTION_DETAILS[:-1]],
            self.preferences["date_format"],
        )
        self.views = [*form_views, self.summary_view]
        self.review_index = len(form_views)

        self._hide_embedded_save_controls()
        self._build_layout()
        self.telephone_screening_view.screening_saved.connect(self.refresh_data)

        for index, view in enumerate(self.views):
            self._saved_states[index] = self._input_state(view)
            self._connect_input_tracking(view)

        self._tracking_enabled = True
        self._show_step(0)
        self.refresh_data()
        self._update_save_status()

    def _build_layout(self) -> None:
        content = QVBoxLayout(self)
        content.setContentsMargins(24, 20, 24, 20)
        content.setSpacing(10)

        self.progress = FormProgress()
        content.addWidget(self.progress)
        self.step_label = QLabel()
        self.step_label.setObjectName("WorkspaceMuted")
        content.addWidget(self.step_label)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(20)
        self.section_title = QLabel()
        self.section_title.setObjectName("WorkspaceTitle")
        heading_row.addWidget(self.section_title)
        heading_row.addStretch()

        self.form_status_label = QLabel()
        heading_row.addWidget(self.form_status_label)
        self.delete_button = QPushButton("Delete patient")
        self.delete_button.setObjectName("WorkspaceDelete")
        self.delete_button.setAutoDefault(False)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(self.delete_current_patient)
        heading_row.addWidget(self.delete_button)
        content.addLayout(heading_row)

        self.section_subtitle = QLabel()
        self.section_subtitle.setObjectName("WorkspaceMuted")
        self.section_subtitle.setWordWrap(True)
        content.addWidget(self.section_subtitle)

        self.pages = QStackedWidget()
        for view in self.views:
            self.pages.addWidget(self._scrollable_page(view))
        content.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        footer.setSpacing(20)
        self.save_status = QLabel("All changes saved")
        self.save_status.setObjectName("WorkspaceMuted")
        footer.addWidget(self.save_status, 1, Qt.AlignmentFlag.AlignBottom)

        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("WorkspaceBack")
        self.back_button.setAutoDefault(False)
        self.back_button.clicked.connect(self.go_back)
        footer.addWidget(self.back_button)
        self.save_button = QPushButton("Save and Continue")
        self.save_button.setObjectName("WorkspaceSave")
        self.save_button.setDefault(True)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_and_continue)
        footer.addWidget(self.save_button)
        content.addLayout(footer)

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

    def _reload_view(self, index: int, *, preserve_drafts: bool = False) -> None:
        view = self.views[index]
        loader = getattr(view, "load_existing_data", None)
        if not callable(loader):
            return

        previous = self._saved_states.get(index, ())
        draft = self._input_state(view)
        has_draft = preserve_drafts and draft != previous
        if has_draft:
            self._restore_input_state(view, previous)
        self._tracking_enabled = False
        try:
            loader()
        finally:
            self._tracking_enabled = True
        self._saved_states[index] = self._input_state(view)
        if has_draft:
            merged = tuple(
                edited if edited != saved else fresh
                for edited, saved, fresh in zip(
                    draft, previous, self._saved_states[index]
                )
            )
            self._restore_input_state(view, merged)

    def _mark_unsaved(self, *_args) -> None:
        if self._tracking_enabled:
            self._update_save_status()
            self.refresh_button_state()

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

    def _show_step(self, target_index: int) -> None:
        if target_index == self.review_index:
            for index in range(self.review_index):
                self._reload_view(index, preserve_drafts=True)
        self._reload_view(target_index, preserve_drafts=True)
        self._current_index = target_index
        self.pages.setCurrentIndex(target_index)
        self._update_section_header(target_index)
        self.progress.set_current_step(target_index)
        self.step_label.setText(f"Step {target_index + 1} of {len(self.views)}")
        self.back_button.setEnabled(target_index > 0)
        self.save_button.setText(
            "Mark as Complete"
            if target_index == self.review_index
            else "Save and Continue"
        )
        self.refresh_button_state()
        self._update_save_status()

    def go_back(self) -> None:
        if self._current_index > 0:
            self._show_step(self._current_index - 1)

    def save_and_continue(self) -> bool:
        if self._current_index == self.review_index:
            return self.complete_form()
        if not self.save_current_section():
            return False
        self._completed_steps.add(self._current_index)
        self._show_step(self._current_index + 1)
        return True

    def save_current_section(self) -> bool:
        view = self.views[self._current_index]
        saver = getattr(view, "save", None)
        if not callable(saver):
            return True

        changed = self._input_state(view) != self._saved_states[self._current_index]
        try:
            if view is self.mullen_view and not view.has_answers():
                saved = True
            else:
                saved = saver(show_confirmation=False)
            if saved is not False and changed and self.is_complete():
                update_patient_form(self.patient_id, "Pending")
        except (ValueError, sqlite3.Error, OSError) as exc:
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

    def complete_form(self) -> bool:
        if self._current_index != self.review_index or self._completed_steps != set(
            range(self.review_index)
        ):
            return False
        if any(
            self._input_state(view) != self._saved_states[index]
            for index, view in enumerate(self.views[: self.review_index])
        ):
            return False
        screener = self.summary_view.screener_input.text().strip()
        if not screener:
            self.summary_view.screener_input.setFocus()
            return False
        try:
            complete_patient_form(self.patient_id, screener)
        except (ValueError, sqlite3.Error, OSError) as exc:
            QMessageBox.warning(self, "Unable to complete form", str(exc))
            return False
        self._saved_states[self.review_index] = self._input_state(self.summary_view)
        self.accept()
        return True

    def refresh_button_state(self) -> None:
        on_review = self._current_index == self.review_index
        self.save_button.setEnabled(
            not on_review
            or (
                bool(self.summary_view.screener_input.text().strip())
                and self._completed_steps == set(range(self.review_index))
                and all(
                    self._input_state(view) == self._saved_states[index]
                    for index, view in enumerate(self.views[: self.review_index])
                )
            )
        )

    def is_complete(self) -> bool:
        return self.patient.get("form_status") == "Complete"

    def refresh_data(self, *_args) -> None:
        self.patient = get_patient(self.patient_id) or {}
        subject_id = self.patient.get("subject_id") or str(self.patient_id)
        self.setWindowTitle(f"Patient {subject_id}")
        self.form_status_label.setText(
            f"Form status: {self.patient.get('form_status') or 'Pending'}"
        )
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
            for index, view in enumerate(self.views):
                if self._input_state(view) != self._saved_states[index]:
                    self._show_step(index)
                    if not self.save_current_section():
                        return False
            return True
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
