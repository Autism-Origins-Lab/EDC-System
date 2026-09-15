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

        tabs.currentChanged.connect(self.refresh_data)

        #adding a mark complete button so that it's marked complete for manual review
        self.mark_complete_button = QPushButton()
        self.mark_complete_button.setObjectName("Mark_Complete_Button")

        self.mark_complete_button.clicked.connect(self.mark_or_unmark_completion)
        layout.addWidget(self.mark_complete_button)
        self.refresh_button_state()


 
    
        """
        Problems:
        1. The first loop never exits even if you mark it eligible, because "eligibility" is always empty.
        """

    @staticmethod
    def button_style(bg_color: str) -> str:
         return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #FFFFFF;
                border-radius: 20px;
                padding: 12px 16px;
            }}
        """
    def mark_or_unmark_completion(self) -> None: #function to set the status as Pending or Complete.
        new_status = "Pending" if self.is_complete() else "Complete"
        self.patient = self.patient or {}
        self.patient["form_status"] = new_status
        update_patient_form(self.patient_id, new_status)
        self.form_status_label.setText(new_status)

        self.refresh_button_state()


    def refresh_button_state(self) -> None: #UI checks if a patient is eligible & if the form has already been marked as complete.
         eligible = self.is_eligible()
         complete = self.is_complete()

         if not eligible:
              self.mark_complete_button.setEnabled(False)
              self.mark_complete_button.setStyleSheet(self.button_style("#696969"))
              self.mark_complete_button.setText("Must Be Eligible to Mark Complete")
         elif complete:
              self.mark_complete_button.setEnabled(True)
              self.mark_complete_button.setStyleSheet(self.button_style("#D82454"))
              self.mark_complete_button.setText("Unmark Complete")
         else:
            self.mark_complete_button.setEnabled(True)
            self.mark_complete_button.setStyleSheet(self.button_style("#44CCAA")) 
            self.mark_complete_button.setText("Mark Complete")
    

    def is_eligible(self):
         eligibility_status = self.patient.get("eligibility") if self.patient else None
         if eligibility_status == "Yes":
              return True
         return False
         
    def is_complete(self):
           current_status = self.patient.get("form_status") if self.patient else None
           if current_status == "Complete":
                return True
           return False
    
    def refresh_data(self, index: int): #function to refresh the overview tab with the new updated form status & eligibility
         if index == 0:  #check if the tab is the overview.
            self.patient = get_patient(self.patient_id) or {}
            self.eligibility_label.setText(self.patient.get("eligibility") or "Not started")
            self.form_status_label.setText(self.patient.get("form_status") or "Pending")
            self.refresh_button_state() #calls the UI change to the button after new status
         

    def _build_overview(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()

        patient = self.patient or {}

        self.form_status_label = QLabel(patient.get("form_status") or "Pending")
        self.eligibility_label = QLabel(patient.get("eligibility") or "Telephone Screening Not Working") #issue
        

        form.addRow("Subject ID", QLabel(patient.get("subject_id", "")))
        form.addRow("Child Name", QLabel(patient.get("child_name") or "Not entered"))
        form.addRow("Date of Birth", QLabel(patient.get("date_of_birth") or "Not entered"))
        form.addRow("Sex", QLabel(patient.get("sex") or "Not entered"))
        form.addRow("Race", QLabel(patient.get("race") or "Not entered"))
        form.addRow("Eligibility", self.eligibility_label) 
        form.addRow("Form Status", self.form_status_label) #add the label to display whether this form is pending or complete

        layout.addLayout(form)
        layout.addStretch()
        return page
