from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.forms import (
    get_family_medical_history,
    save_family_medical_history,
)
from app.ui.components.yes_no_input import YesNoInput


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
        self.family_psychiatric_input = YesNoInput("Family psychiatric diagnosis")
        self.family_psychiatric_description_input = QTextEdit()
        self.family_psychiatric_description_input.setFixedHeight(80)
        self.parent_autism_input = YesNoInput("Mother or father diagnosed with autism")
        self.parent_schizophrenia_input = YesNoInput("Mother or father diagnosed with schizophrenia")
        self.parent_learning_disability_input = YesNoInput(
            "Mother or father diagnosed with learning/intellectual disability"
        )
        self.parent_substance_abuse_input = YesNoInput("Mother or father has substance abuse history")
        self.has_siblings_input = YesNoInput("Child has siblings")
        self.sibling_autism_input = YesNoInput("Sibling diagnosed with autism")
        self.sibling_adhd_input = YesNoInput("Sibling diagnosed with ADHD")
        self.same_father_input = YesNoInput("Same biological father as older sibling")
        self.same_mother_input = YesNoInput("Same biological mother as older sibling")

        self.family_psychiatric_input.add_to_form(form)
        form.addRow("Psychiatric History Description", self.family_psychiatric_description_input)
        self.parent_autism_input.add_to_form(form)
        self.parent_schizophrenia_input.add_to_form(form)
        self.parent_learning_disability_input.add_to_form(form)
        self.parent_substance_abuse_input.add_to_form(form)
        self.has_siblings_input.add_to_form(form)
        self.sibling_autism_input.add_to_form(form)
        self.sibling_adhd_input.add_to_form(form)
        self.same_father_input.add_to_form(form)
        self.same_mother_input.add_to_form(form)

        save_button = QPushButton("Save Family Medical History")
        save_button.setCursor(Qt.PointingHandCursor)
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

        self.family_psychiatric_input.set_value(data.get("family_psychiatric"))
        self.family_psychiatric_description_input.setPlainText(
            data.get("family_psychiatric_description") or ""
        )
        self.parent_autism_input.set_value(data.get("parent_autism"))
        self.parent_schizophrenia_input.set_value(data.get("parent_schizophrenia"))
        self.parent_learning_disability_input.set_value(data.get("parent_learning_disability"))
        self.parent_substance_abuse_input.set_value(data.get("parent_substance_abuse"))
        self.has_siblings_input.set_value(data.get("has_siblings"))
        self.sibling_autism_input.set_value(data.get("sibling_autism"))
        self.sibling_adhd_input.set_value(data.get("sibling_adhd"))
        self.same_father_input.set_value(data.get("same_father_as_older_sibling"))
        self.same_mother_input.set_value(data.get("same_mother_as_older_sibling"))

    def collect_data(self) -> dict:
        return {
            "family_psychiatric": self.family_psychiatric_input.value(),
            "family_psychiatric_description": (
                self.family_psychiatric_description_input.toPlainText().strip()
            ),
            "parent_autism": self.parent_autism_input.value(),
            "parent_schizophrenia": self.parent_schizophrenia_input.value(),
            "parent_learning_disability": self.parent_learning_disability_input.value(),
            "parent_substance_abuse": self.parent_substance_abuse_input.value(),
            "has_siblings": self.has_siblings_input.value(),
            "sibling_autism": self.sibling_autism_input.value(),
            "sibling_adhd": self.sibling_adhd_input.value(),
            "same_father_as_older_sibling": self.same_father_input.value(),
            "same_mother_as_older_sibling": self.same_mother_input.value(),
        }

    def save(self, *, show_confirmation=True) -> bool:
        save_family_medical_history(self.patient_id, self.collect_data())
        if show_confirmation:
            QMessageBox.information(self, "Saved", "Family medical history saved successfully.")
        return True
