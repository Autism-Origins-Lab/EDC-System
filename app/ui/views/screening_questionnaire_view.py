from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import (
    get_screening_questionnaire,
    save_screening_questionnaire,
)
from app.database.queries.patients import update_patient


class ScreeningQuestionnaireView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id

        outer_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        form = QFormLayout()
        self.parent_name_input = QLineEdit()
        self.child_name_input = QLineEdit()
        self.date_of_birth_input = QLineEdit()
        self.age_input = QLineEdit()
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["", "Female", "Male", "Other", "Prefer not to answer"])
        self.race_input = QLineEdit()
        self.address_input = QLineEdit()
        self.city_input = QLineEdit()
        self.state_input = QLineEdit()
        self.zip_code_input = QLineEdit()
        self.home_phone_input = QLineEdit()
        self.work_phone_input = QLineEdit()
        self.best_time_to_call_input = QLineEdit()
        self.fax_input = QLineEdit()
        self.email_input = QLineEdit()
        self.mother_name_input = QLineEdit()
        self.father_name_input = QLineEdit()
        self.mother_age_input = QLineEdit()
        self.father_age_input = QLineEdit()
        self.biological_mother_checkbox = QCheckBox("Mother listed is biological mother")
        self.biological_mother_name_input = QLineEdit()
        self.biological_father_checkbox = QCheckBox("Father listed is biological father")
        self.biological_father_name_input = QLineEdit()
        self.research_participation_checkbox = QCheckBox("Family has participated in research")
        self.research_study_input = QLineEdit()
        self.research_study_when_input = QLineEdit()
        self.research_study_where_input = QLineEdit()

        form.addRow("Parent Name", self.parent_name_input)
        form.addRow("Child Name", self.child_name_input)
        form.addRow("Date of Birth", self.date_of_birth_input)
        form.addRow("Age", self.age_input)
        form.addRow("Sex", self.sex_combo)
        form.addRow("Race", self.race_input)
        form.addRow("Address", self.address_input)
        form.addRow("City", self.city_input)
        form.addRow("State", self.state_input)
        form.addRow("Zip Code", self.zip_code_input)
        form.addRow("Home Phone", self.home_phone_input)
        form.addRow("Work Phone", self.work_phone_input)
        form.addRow("Best Time To Call", self.best_time_to_call_input)
        form.addRow("Fax", self.fax_input)
        form.addRow("Email", self.email_input)
        form.addRow("Mother Name", self.mother_name_input)
        form.addRow("Father Name", self.father_name_input)
        form.addRow("Mother Age", self.mother_age_input)
        form.addRow("Father Age", self.father_age_input)
        form.addRow("", self.biological_mother_checkbox)
        form.addRow("Biological Mother Name", self.biological_mother_name_input)
        form.addRow("", self.biological_father_checkbox)
        form.addRow("Biological Father Name", self.biological_father_name_input)
        form.addRow("", self.research_participation_checkbox)
        form.addRow("Research Study", self.research_study_input)
        form.addRow("When", self.research_study_when_input)
        form.addRow("Where", self.research_study_where_input)

        save_button = QPushButton("Save Screening Questionnaire")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save)

        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addStretch()
        scroll_area.setWidget(page)
        outer_layout.addWidget(scroll_area)

        self.load_existing_data()

    def load_existing_data(self) -> None:
        data = get_screening_questionnaire(self.patient_id)
        if not data:
            return

        self.parent_name_input.setText(data.get("parent_name") or "")
        self.child_name_input.setText(data.get("child_name") or "")
        self.date_of_birth_input.setText(data.get("date_of_birth") or "")
        self.age_input.setText(data.get("age") or "")
        self.sex_combo.setCurrentText(data.get("sex") or "")
        self.race_input.setText(data.get("race") or "")
        self.address_input.setText(data.get("address") or "")
        self.city_input.setText(data.get("city") or "")
        self.state_input.setText(data.get("state") or "")
        self.zip_code_input.setText(data.get("zip_code") or "")
        self.home_phone_input.setText(data.get("home_phone") or "")
        self.work_phone_input.setText(data.get("work_phone") or "")
        self.best_time_to_call_input.setText(data.get("best_time_to_call") or "")
        self.fax_input.setText(data.get("fax") or "")
        self.email_input.setText(data.get("email") or "")
        self.mother_name_input.setText(data.get("mother_name") or "")
        self.father_name_input.setText(data.get("father_name") or "")
        self.mother_age_input.setText(data.get("mother_age") or "")
        self.father_age_input.setText(data.get("father_age") or "")
        self.biological_mother_checkbox.setChecked(bool(data.get("biological_mother")))
        self.biological_mother_name_input.setText(data.get("biological_mother_name") or "")
        self.biological_father_checkbox.setChecked(bool(data.get("biological_father")))
        self.biological_father_name_input.setText(data.get("biological_father_name") or "")
        self.research_participation_checkbox.setChecked(bool(data.get("research_participation")))
        self.research_study_input.setText(data.get("research_study") or "")
        self.research_study_when_input.setText(data.get("research_study_when") or "")
        self.research_study_where_input.setText(data.get("research_study_where") or "")

    def collect_data(self) -> dict:
        return {
            "parent_name": self.parent_name_input.text().strip(),
            "child_name": self.child_name_input.text().strip(),
            "date_of_birth": self.date_of_birth_input.text().strip(),
            "age": self.age_input.text().strip(),
            "sex": self.sex_combo.currentText(),
            "race": self.race_input.text().strip(),
            "address": self.address_input.text().strip(),
            "city": self.city_input.text().strip(),
            "state": self.state_input.text().strip(),
            "zip_code": self.zip_code_input.text().strip(),
            "home_phone": self.home_phone_input.text().strip(),
            "work_phone": self.work_phone_input.text().strip(),
            "best_time_to_call": self.best_time_to_call_input.text().strip(),
            "fax": self.fax_input.text().strip(),
            "email": self.email_input.text().strip(),
            "mother_name": self.mother_name_input.text().strip(),
            "father_name": self.father_name_input.text().strip(),
            "mother_age": self.mother_age_input.text().strip(),
            "father_age": self.father_age_input.text().strip(),
            "biological_mother": int(self.biological_mother_checkbox.isChecked()),
            "biological_mother_name": self.biological_mother_name_input.text().strip(),
            "biological_father": int(self.biological_father_checkbox.isChecked()),
            "biological_father_name": self.biological_father_name_input.text().strip(),
            "research_participation": int(self.research_participation_checkbox.isChecked()),
            "research_study": self.research_study_input.text().strip(),
            "research_study_when": self.research_study_when_input.text().strip(),
            "research_study_where": self.research_study_where_input.text().strip(),
        }

    def save(self) -> None:
        data = self.collect_data()
        save_screening_questionnaire(self.patient_id, data)
        update_patient(
            self.patient_id,
            {
                "child_name": data["child_name"],
                "date_of_birth": data["date_of_birth"],
                "sex": data["sex"],
                "race": data["race"],
            },
        )
        QMessageBox.information(self, "Saved", "Screening questionnaire saved successfully.")
