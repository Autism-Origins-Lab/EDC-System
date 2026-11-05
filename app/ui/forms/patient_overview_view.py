from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.patients import get_patient, update_patient
from app.services.preferences import DATE_FORMAT, format_date, parse_date
from app.ui.components.date_input import DateInput


class PatientOverviewView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        participant = QGroupBox("Participant")
        form = QFormLayout(participant)
        form.setContentsMargins(26, 30, 26, 26)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.subject_id_input = QLineEdit()
        self.child_name_input = QLineEdit()
        self.date_of_birth_input = QLineEdit()
        self.date_of_birth_input.setPlaceholderText(self.date_format)
        
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["", "Female", "Male", "Other", "Prefer not to answer"])
        
        self.base_races = ["", "Asian", "Black or African American", "Native American", "Native Hawaiian or Pacific Islander", "White", "Other"]
        self.race_combo = QComboBox()
        self.race_combo.addItems(self.base_races)
       
        self.other_race_input = QLineEdit()
        self.other_race_input.setPlaceholderText("Please enter race:")
        self.other_race_input.setHidden(True)
        self.race_combo.currentTextChanged.connect(self.check_other_race)
        
        form.addRow("Subject ID", self.subject_id_input)
        form.addRow("Child name", self.child_name_input)
        form.addRow("Date of birth", self.date_of_birth_input)
        form.addRow("Sex", self.sex_combo)
        form.addRow("Race", self.race_combo)
        form.addRow("",self.other_race_input)
        layout.addWidget(participant)

        risk = QGroupBox("Familial risk")
        risk_layout = QVBoxLayout(risk)
        risk_layout.setContentsMargins(32, 28, 26, 24)
        risk_layout.setSpacing(12)
        self.high_risk_checkbox = QCheckBox("High familial risk")
        self.low_risk_checkbox = QCheckBox("Low familial risk")
        self.high_risk_checkbox.toggled.connect(
            lambda checked: (
                self.low_risk_checkbox.setChecked(False) if checked else None
            )
        )
        self.low_risk_checkbox.toggled.connect(
            lambda checked: (
                self.high_risk_checkbox.setChecked(False) if checked else None
            )
        )
        risk_layout.addWidget(self.high_risk_checkbox)
        risk_layout.addWidget(self.low_risk_checkbox)
        layout.addWidget(risk)
        layout.addStretch()
        self.load_existing_data()

    def load_existing_data(self) -> None:
        patient = get_patient(self.patient_id) or {}
        self.subject_id_input.setText(patient.get("subject_id") or "")
        self.child_name_input.setText(patient.get("child_name") or "")
        self.date_of_birth_input.setText(format_date(patient.get("date_of_birth")))
        sex = patient.get("sex") or ""
        if self.sex_combo.findText(sex) < 0:
            self.sex_combo.addItem(sex)
        self.sex_combo.setCurrentText(sex)
        race = patient.get("race") or ""

        if race and race not in self.base_races:
            self.race_combo.setCurrentText("Other")
            self.other_race_input.setText(race)
            self.other_race_input.setHidden(False)
        else:
            self.race_combo.setCurrentText(race)
            self.other_race_input.setHidden(True)
            self.other_race_input.clear()
        self.high_risk_checkbox.setChecked(patient.get("risk") == 1)
        self.low_risk_checkbox.setChecked(patient.get("risk") == 0)

    def check_other_race(self, text):
        if text == "Other":
            self.other_race_input.setHidden(False)
            self.other_race_input.setFocus()
        else:
            self.other_race_input.setHidden(True)
            self.other_race_input.clear()

    def collect_data(self) -> dict:
        selected_race = self.race_combo.currentText()
        if selected_race == "Other":
            final_race = self.other_race_input.text().strip()
        else:
            final_race = selected_race

        return {
            "subject_id": self.subject_id_input.text().strip(),
            "child_name": self.child_name_input.text().strip(),
            "date_of_birth": self.date_of_birth_input.text().strip(),
            "sex": self.sex_combo.currentText(),
            "race": final_race,
            "risk": (
                1
                if self.high_risk_checkbox.isChecked()
                else 0
                if self.low_risk_checkbox.isChecked()
                else None
            ),
        }

    def save(self, *, show_confirmation=True) -> bool:
        data = self.collect_data()
        birthday = data["date_of_birth"]
        if birthday:
            try:
                data["date_of_birth"] = parse_date(birthday)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Unable to save",
                    f"Enter date of birth as {DATE_FORMAT}.",
                )
                return False
        update_patient(self.patient_id, data)
        if show_confirmation:
            QMessageBox.information(self, "Saved", "Patient overview saved successfully.")
        return True
