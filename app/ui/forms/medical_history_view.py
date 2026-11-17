from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.forms import get_medical_history, save_medical_history
from app.ui.components.yes_no_input import YesNoInput


class MedicalHistoryView(QWidget):
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
        self.general_health_input = QTextEdit()
        self.general_health_input.setFixedHeight(80)
        self.seen_neurologist_input = YesNoInput("Seen neurologist")
        self.neurologist_description_input = QTextEdit()
        self.neurologist_description_input.setFixedHeight(80)
        self.head_injury_input = YesNoInput("Head injury")
        self.head_injury_description_input = QTextEdit()
        self.head_injury_description_input.setFixedHeight(80)
        self.genetic_abnormalities_input = YesNoInput("Genetic abnormalities")
        self.genetic_abnormalities_description_input = QTextEdit()
        self.genetic_abnormalities_description_input.setFixedHeight(80)
        self.seizure_epileptic_attack_input = YesNoInput("Seizure or epileptic attack")
        self.gestational_age_input = QLineEdit()
        self.birthweight_input = QLineEdit()
        self.birthlength_input = QLineEdit()
        self.pregnancy_complications_input = YesNoInput("Pregnancy or birth complications")
        self.pregnancy_complications_description_input = QTextEdit()
        self.pregnancy_complications_description_input.setFixedHeight(80)

        form.addRow("General Health", self.general_health_input)
        self.seen_neurologist_input.add_to_form(form)
        form.addRow("Neurologist Description", self.neurologist_description_input)
        self.head_injury_input.add_to_form(form)
        form.addRow("Head Injury Description", self.head_injury_description_input)
        self.genetic_abnormalities_input.add_to_form(form)
        form.addRow("Genetic Abnormalities Description", self.genetic_abnormalities_description_input)
        self.seizure_epileptic_attack_input.add_to_form(form)
        form.addRow("Gestational Age", self.gestational_age_input)
        form.addRow("Birthweight", self.birthweight_input)
        form.addRow("Birthlength", self.birthlength_input)
        self.pregnancy_complications_input.add_to_form(form)
        form.addRow("Complications Description", self.pregnancy_complications_description_input)

        save_button = QPushButton("Save Medical History")
        save_button.setObjectName("PrimaryButton")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self.save)

        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addStretch()
        scroll_area.setWidget(page)
        outer_layout.addWidget(scroll_area)

        self.load_existing_data()

    def load_existing_data(self) -> None:
        data = get_medical_history(self.patient_id)
        if not data:
            return

        self.general_health_input.setPlainText(data.get("general_health") or "")
        self.seen_neurologist_input.set_value(data.get("seen_neurologist"))
        self.neurologist_description_input.setPlainText(data.get("neurologist_description") or "")
        self.head_injury_input.set_value(data.get("head_injury"))
        self.head_injury_description_input.setPlainText(data.get("head_injury_description") or "")
        self.genetic_abnormalities_input.set_value(data.get("genetic_abnormalities"))
        self.genetic_abnormalities_description_input.setPlainText(
            data.get("genetic_abnormalities_description") or ""
        )
        self.seizure_epileptic_attack_input.set_value(data.get("seizure_epileptic_attack"))
        self.gestational_age_input.setText(data.get("gestational_age") or "")
        self.birthweight_input.setText(data.get("birthweight") or "")
        self.birthlength_input.setText(data.get("birthlength") or "")
        self.pregnancy_complications_input.set_value(data.get("pregnancy_complications"))
        self.pregnancy_complications_description_input.setPlainText(
            data.get("pregnancy_complications_description") or ""
        )

    def collect_data(self) -> dict:
        return {
            "general_health": self.general_health_input.toPlainText().strip(),
            "seen_neurologist": self.seen_neurologist_input.value(),
            "neurologist_description": self.neurologist_description_input.toPlainText().strip(),
            "head_injury": self.head_injury_input.value(),
            "head_injury_description": self.head_injury_description_input.toPlainText().strip(),
            "genetic_abnormalities": self.genetic_abnormalities_input.value(),
            "genetic_abnormalities_description": (
                self.genetic_abnormalities_description_input.toPlainText().strip()
            ),
            "seizure_epileptic_attack": self.seizure_epileptic_attack_input.value(),
            "gestational_age": self.gestational_age_input.text().strip(),
            "birthweight": self.birthweight_input.text().strip(),
            "birthlength": self.birthlength_input.text().strip(),
            "pregnancy_complications": self.pregnancy_complications_input.value(),
            "pregnancy_complications_description": (
                self.pregnancy_complications_description_input.toPlainText().strip()
            ),
        }

    def save(self, *, show_confirmation=True) -> bool:
        save_medical_history(self.patient_id, self.collect_data())
        if show_confirmation:
            QMessageBox.information(self, "Saved", "Medical history saved successfully.")
        return True
