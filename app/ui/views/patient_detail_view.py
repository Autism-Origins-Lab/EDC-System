from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

"""Issues I want to consider:
1. the mark complete button should be completely independent from eligibility. If it is marked complete, then it should be put into a ready export.
    -> I think i might need to add another variable called "complete" form in the data base.
    ///
3. a section to review all of the form inputs & section before finalizing changes
4. when a form is "complete" and marked ready to export, and i want to make changes to it, it should update what needs to be exported already.
2. what fields need to be filled out for something to be marked complete? so it also does it automatically? worry abt later

Accomplished:
Added metric cards to display information in a friendlier way
Display form information below (Eligibility, Name, ID)
Testing UI and changing cursor on elements that are clickable
I created a mark eligibility button that manually marks a form complete, but I'm tweaking that because I realized that it could pose a lot of problems later on while testing it out
Working on EDC system & more vizualizations 
"""

from app.database.queries.patients import get_patient, update_patient_form
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

        #adding a mark complete button so that it's marked complete for manual review
        self.mark_complete_button = QPushButton("Must Be Eligible to Mark Complete")
        self.mark_complete_button.setObjectName("Mark_Complete_Button")
        self.mark_complete_button.setCursor(Qt.PointingHandCursor) #make it look clickable

        #if the patient is NOT eligible, the button is grayed out. 
        while not self.is_eligible:
             self.mark_complete_button.setStyleSheet(self.complete_button_style("#696969"))
             if self.is_eligible: 
                  break #the patient is eligible, so break out of this loop.

        """
        Problems:
        1. The first loop never exits even if you mark it eligible, because "eligibility" is always empty.
        """

        while not self.is_complete: #while the patient's form is not marked complete,
            self.mark_complete_button.setStyleSheet(self.complete_button_style("#44CCAA")) #the button should be colorful
            self.mark_complete_button.clicked.connect(self.mark_complete) #it should be able to be marked complete
            if self.is_complete: #the form is already complete, so now break out the loop
                  self.mark_complete_button.setStyleSheet(self.complete_button_style("#D82454")) #once the loop is broken out of, (the patient is still eligible)
                  self.mark_complete_button.setText("Unmark Complete")
                  self.mark_complete_button.clicked.connect(self.unmark_complete) 

        layout.addWidget(self.mark_complete_button)

    @staticmethod
    def complete_button_style(bg_color: str) -> str:
         return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #FFFFFF;
                border-radius: 20px;
                padding: 12px 16px;
            }}
        """

    def is_eligible(self):
         eligibility_status = self.patient.get("eligibility") if self.patient else None
         if eligibility_status == "Yes":
              return True
         
    def is_complete(self):
           current_status = self.patient.get("form_progress") if self.patient else None
           if current_status == "Complete":
                return True
         
    def mark_complete(self):
        update_patient_form(self.patient_id, "Complete") #call database method

        if self.patient:
            self.patient["form_status"] = "Complete"

        self.mark_complete_button.setText("Unmark Complete")
        self.mark_complete_button.clicked.connect(self.unmark_complete) 

    def unmark_complete(self):
        update_patient_form(self.patient_id, "Pending") #call database method

        if self.patient:
                    self.patient["form_status"] = "Pending"
        self.mark_complete_button.setText("Mark Complete")
        self.mark_complete_button.clicked.connect(self.mark_complete) 

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
        form.addRow("Eligibility", QLabel(patient.get("eligibility")))
        form.addRow("Form Status", QLabel(patient.get("form_status"))) #add the label to display whether this form is pending or complete

        layout.addLayout(form)
        layout.addStretch()
        return page
