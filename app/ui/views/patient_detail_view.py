from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.patients import get_patient
from app.ui.views.family_medical_history_view import FamilyMedicalHistoryView
from app.ui.views.medical_history_view import MedicalHistoryView
from app.ui.views.procedure_schedule_view import ProcedureScheduleView
from app.ui.views.screening_questionnaire_view import ScreeningQuestionnaireView
from app.ui.views.telephone_screening_view import TelephoneScreeningView


class PatientDetailView(QDialog):
    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient = get_patient(patient_id)

        subject_id = self.patient["subject_id"] if self.patient else str(patient_id)
        self.setWindowTitle(f"Patient {subject_id}")
        self.resize(900, 680)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_overview(), "Overview")
        tabs.addTab(TelephoneScreeningView(patient_id), "Telephone Screening")
        tabs.addTab(ScreeningQuestionnaireView(patient_id), "Screening Questionnaire")
        tabs.addTab(MedicalHistoryView(patient_id), "Medical History")
        tabs.addTab(FamilyMedicalHistoryView(patient_id), "Family Medical History")
        tabs.addTab(ProcedureScheduleView(patient_id), "Procedure Schedule")

        layout.addWidget(tabs)

    def _build_overview(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()

        patient = self.patient or {}
        form.addRow("Subject ID", QLabel(patient.get("subject_id", "")))
        form.addRow("Child Name", QLabel(patient.get("child_name") or "Not entered"))
        form.addRow("Date of Birth", QLabel(patient.get("date_of_birth") or "Not entered"))
        form.addRow("Sex", QLabel(patient.get("sex") or "Not entered"))
        form.addRow("Race", QLabel(patient.get("race") or "Not entered"))

        layout.addLayout(form)
        layout.addStretch()
        return page
