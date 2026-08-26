from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import get_telephone_screening, save_telephone_screening


class TelephoneScreeningView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        form = QFormLayout()

        self.screening_date_input = QLineEdit()
        self.appointment_date_input = QLineEdit()
        self.screener_input = QLineEdit()

        self.eligibility_combo = QComboBox()
        self.eligibility_combo.addItems(["", "Yes", "No"])

        self.high_risk_checkbox = QCheckBox("High familial risk")
        self.low_risk_checkbox = QCheckBox("Low familial risk")

        self.schedule_date_input = QLineEdit()
        self.birthweight_input = QLineEdit()
        self.gestational_input = QLineEdit()

        self.verbal_consent_combo = QComboBox()
        self.verbal_consent_combo.addItems(["", "Yes", "No"])

        self.initials_input = QLineEdit()

        form.addRow("Screening Date", self.screening_date_input)
        form.addRow("Appointment Date", self.appointment_date_input)
        form.addRow("Screener", self.screener_input)
        form.addRow("Eligible for Participation", self.eligibility_combo)
        form.addRow("", self.high_risk_checkbox)
        form.addRow("", self.low_risk_checkbox)
        form.addRow("Schedule Date", self.schedule_date_input)
        form.addRow("Birthweight", self.birthweight_input)
        form.addRow("Gestational Age", self.gestational_input)
        form.addRow("Verbal Consent", self.verbal_consent_combo)
        form.addRow("Consent Initials", self.initials_input)

        self.save_button = QPushButton("Save Telephone Screening")
        self.save_button.clicked.connect(self.save)

        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addStretch()

        self.load_existing_data()

    def load_existing_data(self) -> None:
        data = get_telephone_screening(self.patient_id)
        if not data:
            return

        self.screening_date_input.setText(data.get("screening_date") or "")
        self.appointment_date_input.setText(data.get("appointment_date") or "")
        self.screener_input.setText(data.get("screener") or "")
        self.eligibility_combo.setCurrentText(data.get("eligibility") or "")
        self.high_risk_checkbox.setChecked(bool(data.get("high_familial_risk")))
        self.low_risk_checkbox.setChecked(bool(data.get("low_familial_risk")))
        self.schedule_date_input.setText(data.get("schedule_date") or "")
        self.birthweight_input.setText(data.get("birthweight") or "")
        self.gestational_input.setText(data.get("gestational") or "")

        consent = data.get("verbal_consent")
        if consent is None:
            self.verbal_consent_combo.setCurrentText("")
        else:
            self.verbal_consent_combo.setCurrentText("Yes" if consent else "No")

        self.initials_input.setText(data.get("consent_initials") or "")

    def collect_data(self) -> dict:
        consent_text = self.verbal_consent_combo.currentText()

        if consent_text == "Yes":
            verbal_consent = 1
        elif consent_text == "No":
            verbal_consent = 0
        else:
            verbal_consent = None

        return {
            "screening_date": self.screening_date_input.text().strip(),
            "appointment_date": self.appointment_date_input.text().strip(),
            "screener": self.screener_input.text().strip(),
            "eligibility": self.eligibility_combo.currentText(),
            "high_familial_risk": int(self.high_risk_checkbox.isChecked()),
            "low_familial_risk": int(self.low_risk_checkbox.isChecked()),
            "schedule_date": self.schedule_date_input.text().strip(),
            "birthweight": self.birthweight_input.text().strip(),
            "gestational": self.gestational_input.text().strip(),
            "verbal_consent": verbal_consent,
            "consent_initials": self.initials_input.text().strip(),
        }

    def save(self) -> None:
        save_telephone_screening(self.patient_id, self.collect_data())

        QMessageBox.information(
            self,
            "Saved",
            "Telephone screening saved successfully.",
        )