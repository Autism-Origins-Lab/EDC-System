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
from app.services.preferences import format_date, load_preferences, parse_date


class PatientOverviewView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id
        self.date_format = load_preferences()["date_format"]
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
        self.race_input = QLineEdit()
        form.addRow("Subject ID", self.subject_id_input)
        form.addRow("Child name", self.child_name_input)
        form.addRow("Date of birth", self.date_of_birth_input)
        form.addRow("Sex", self.sex_combo)
        form.addRow("Race", self.race_input)
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
        self.date_of_birth_input.setText(
            format_date(patient.get("date_of_birth"), self.date_format)
        )
        sex = patient.get("sex") or ""
        if self.sex_combo.findText(sex) < 0:
            self.sex_combo.addItem(sex)
        self.sex_combo.setCurrentText(sex)
        self.race_input.setText(patient.get("race") or "")
        self.high_risk_checkbox.setChecked(patient.get("risk") == 1)
        self.low_risk_checkbox.setChecked(patient.get("risk") == 0)

    def collect_data(self) -> dict:
        return {
            "subject_id": self.subject_id_input.text().strip(),
            "child_name": self.child_name_input.text().strip(),
            "date_of_birth": self.date_of_birth_input.text().strip(),
            "sex": self.sex_combo.currentText(),
            "race": self.race_input.text().strip(),
            "risk": (
                1
                if self.high_risk_checkbox.isChecked()
                else 0
                if self.low_risk_checkbox.isChecked()
                else None
            ),
        }

    def save(self) -> bool:
        data = self.collect_data()
        birthday = data["date_of_birth"]
        if birthday:
            try:
                data["date_of_birth"] = parse_date(birthday, self.date_format)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Unable to save",
                    f"Enter date of birth as {self.date_format}.",
                )
                return False
        update_patient(self.patient_id, data)
        return True
