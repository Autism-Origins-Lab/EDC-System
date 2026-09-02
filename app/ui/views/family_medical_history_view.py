from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import (
    get_family_medical_history,
    save_family_medical_history,
)


class FamilyMedicalHistoryView(QWidget):
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
        self.family_psychiatric_checkbox = QCheckBox("Family psychiatric diagnosis")
        self.family_psychiatric_description_input = QTextEdit()
        self.family_psychiatric_description_input.setFixedHeight(80)
        self.parent_autism_checkbox = QCheckBox("Mother or father diagnosed with autism")
        self.parent_schizophrenia_checkbox = QCheckBox("Mother or father diagnosed with schizophrenia")
        self.parent_learning_disability_checkbox = QCheckBox(
            "Mother or father diagnosed with learning/intellectual disability"
        )
        self.parent_substance_abuse_checkbox = QCheckBox("Mother or father has substance abuse history")
        self.has_siblings_checkbox = QCheckBox("Child has siblings")
        self.sibling_autism_checkbox = QCheckBox("Sibling diagnosed with autism")
        self.sibling_adhd_checkbox = QCheckBox("Sibling diagnosed with ADHD")
        self.same_father_checkbox = QCheckBox("Same biological father as older sibling")
        self.same_mother_checkbox = QCheckBox("Same biological mother as older sibling")

        form.addRow("", self.family_psychiatric_checkbox)
        form.addRow("Psychiatric History Description", self.family_psychiatric_description_input)
        form.addRow("", self.parent_autism_checkbox)
        form.addRow("", self.parent_schizophrenia_checkbox)
        form.addRow("", self.parent_learning_disability_checkbox)
        form.addRow("", self.parent_substance_abuse_checkbox)
        form.addRow("", self.has_siblings_checkbox)
        form.addRow("", self.sibling_autism_checkbox)
        form.addRow("", self.sibling_adhd_checkbox)
        form.addRow("", self.same_father_checkbox)
        form.addRow("", self.same_mother_checkbox)

        save_button = QPushButton("Save Family Medical History")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save)

        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addStretch()
        scroll_area.setWidget(page)
        outer_layout.addWidget(scroll_area)

        self.load_existing_data()

    def load_existing_data(self) -> None:
        data = get_family_medical_history(self.patient_id)
        if not data:
            return

        self.family_psychiatric_checkbox.setChecked(bool(data.get("family_psychiatric")))
        self.family_psychiatric_description_input.setPlainText(
            data.get("family_psychiatric_description") or ""
        )
        self.parent_autism_checkbox.setChecked(bool(data.get("parent_autism")))
        self.parent_schizophrenia_checkbox.setChecked(bool(data.get("parent_schizophrenia")))
        self.parent_learning_disability_checkbox.setChecked(
            bool(data.get("parent_learning_disability"))
        )
        self.parent_substance_abuse_checkbox.setChecked(bool(data.get("parent_substance_abuse")))
        self.has_siblings_checkbox.setChecked(bool(data.get("has_siblings")))
        self.sibling_autism_checkbox.setChecked(bool(data.get("sibling_autism")))
        self.sibling_adhd_checkbox.setChecked(bool(data.get("sibling_adhd")))
        self.same_father_checkbox.setChecked(bool(data.get("same_father_as_older_sibling")))
        self.same_mother_checkbox.setChecked(bool(data.get("same_mother_as_older_sibling")))

    def collect_data(self) -> dict:
        return {
            "family_psychiatric": int(self.family_psychiatric_checkbox.isChecked()),
            "family_psychiatric_description": (
                self.family_psychiatric_description_input.toPlainText().strip()
            ),
            "parent_autism": int(self.parent_autism_checkbox.isChecked()),
            "parent_schizophrenia": int(self.parent_schizophrenia_checkbox.isChecked()),
            "parent_learning_disability": int(self.parent_learning_disability_checkbox.isChecked()),
            "parent_substance_abuse": int(self.parent_substance_abuse_checkbox.isChecked()),
            "has_siblings": int(self.has_siblings_checkbox.isChecked()),
            "sibling_autism": int(self.sibling_autism_checkbox.isChecked()),
            "sibling_adhd": int(self.sibling_adhd_checkbox.isChecked()),
            "same_father_as_older_sibling": int(self.same_father_checkbox.isChecked()),
            "same_mother_as_older_sibling": int(self.same_mother_checkbox.isChecked()),
        }

    def save(self) -> None:
        save_family_medical_history(self.patient_id, self.collect_data())
        QMessageBox.information(self, "Saved", "Family medical history saved successfully.")
