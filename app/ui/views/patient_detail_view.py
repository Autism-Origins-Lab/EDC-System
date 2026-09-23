from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

"""Issues I want to consider:
1. make updates happen when overview clicked.
3. a section to review all of the form inputs & section before finalizing changes
4. when a form is "complete" and marked ready to export, and i want to make changes to it, it should update what needs to be exported already.
2. what fields need to be filled out for something to be marked complete? so it also does it automatically? worry abt later
what if patients were already marked complete with eligibiilty issues. should i write logic to revert them..?

Accomplished:
Added metric cards to display information in a friendlier way --> changed to donut chart. 
Display form information below (Eligibility, Name, ID)
Testing UI and changing cursor on elements that are clickable
I created a mark eligibility button that manually marks a form complete, but I'm tweaking that -> 
"""

from app.database.queries.patients import get_patient, update_patient_form
from app.ui.views.family_medical_history_view import FamilyMedicalHistoryView
from app.ui.views.medical_history_view import MedicalHistoryView
from app.ui.views.procedure_schedule_view import ProcedureScheduleView
from app.ui.views.screening_questionnaire_view import ScreeningQuestionnaireView
from app.ui.views.telephone_screening_view import TelephoneScreeningView

# import Mullen class 
from app.ui.views.mullen_view import MullenView

class PatientDetailView(QDialog):
    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient = get_patient(patient_id)

        self.telephone_screening_view = TelephoneScreeningView(self.patient_id)
        self.telephone_screening_view.screening_saved.connect(self.refresh_data)

        subject_id = self.patient["subject_id"] if self.patient else str(patient_id)
        self.setWindowTitle(f"Patient {subject_id}")
        self.resize(800, 800)

        layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        top_bar.addStretch()

        tabs = QTabWidget()
        tabs.setUsesScrollButtons(False)
        tabs.addTab(self._build_overview(), "Overview")
        tabs.addTab(self.telephone_screening_view, "Telephone Screening")
        tabs.addTab(ScreeningQuestionnaireView(patient_id), "Screening Questionnaire")
        tabs.addTab(MedicalHistoryView(patient_id), "Medical History")
        tabs.addTab(FamilyMedicalHistoryView(patient_id), "Family Medical History")
        tabs.addTab(ProcedureScheduleView(patient_id), "Procedure Schedule")
        tabs.addTab(MullenView(patient_id), "Mullen Assessment")
        layout.addWidget(tabs)

        #adding a mark complete button so that it's marked complete for manual review
        self.mark_complete_button = QPushButton()
        self.mark_complete_button.setObjectName("Mark_Complete_Button")

        self.mark_complete_button.clicked.connect(self.mark_or_unmark_completion)
        top_bar.addWidget(self.mark_complete_button)
        layout.addLayout(top_bar)
        self.refresh_button_state()



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

        self.patient = get_patient(self.patient_id) or {}

        if not self.is_eligible():
             #inelgible = no newly marked complete
             #or should i revert this to pending?
             self.refresh_button_state()
             return 
        
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
              self.mark_complete_button.setCursor(Qt.PointingHandCursor)

         else:
            self.mark_complete_button.setEnabled(True)
            self.mark_complete_button.setStyleSheet(self.button_style("#44CCAA")) 
            self.mark_complete_button.setText("Mark Complete")
            self.mark_complete_button.setCursor(Qt.PointingHandCursor)

    

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
    
    def refresh_data(self, *args) -> None: #function to refresh the overview tab with the new updated form status & eligibility
        self.patient = get_patient(self.patient_id) or {}
        self.eligibility_label.setText(self.patient.get("eligibility") or "Not started")
        self.form_status_label.setText(self.patient.get("form_status") or "Pending")
        self.refresh_button_state() #calls the UI change to the button after new status

    def refresh_overview(self, index: int):
         if index == 0:
            self.patient = get_patient(self.patient_id) or {}
            self.name_label.setText(self.patient.get("child_name") or "Not started")
            self.birth_label.setText(self.patient.get("date_of_birth") or "Pending")
            self.sex_label.setText(self.patient.get("sex") or "Not started")
            self.race_label.setText(self.patient.get("race") or "Pending")
         

    def _build_overview(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()

        patient = self.patient or {}

        self.form_status_label = QLabel(patient.get("form_status") or "Pending")
        self.eligibility_label = QLabel(patient.get("eligibility") or "Not evaluated") 
        self.name_label = QLabel(patient.get("child_name") or "Not entered")
        self.birth_label = QLabel(patient.get("date_of_birth") or "Not entered")
        self.sex_label = QLabel(patient.get("sex") or "Not entered")
        self.race_label = QLabel(patient.get("race") or "Not entered")
        

        form.addRow("Subject ID", QLabel(patient.get("subject_id", "")))
        form.addRow("Child Name", self.name_label)
        form.addRow("Date of Birth", self.birth_label)
        form.addRow("Sex", self.sex_label)
        form.addRow("Race", self.race_label)
        form.addRow("Eligibility", self.eligibility_label) 
        form.addRow("Form Status", self.form_status_label)

        layout.addLayout(form)
        layout.addStretch()
        return page
