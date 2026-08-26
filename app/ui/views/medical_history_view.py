from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import get_medical_history, save_medical_history


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
        self.seen_neurologist_checkbox = QCheckBox("Seen neurologist")
        self.neurologist_description_input = QTextEdit()
        self.neurologist_description_input.setFixedHeight(80)
        self.head_injury_checkbox = QCheckBox("Head injury")
        self.head_injury_description_input = QTextEdit()
        self.head_injury_description_input.setFixedHeight(80)
        self.genetic_abnormalities_checkbox = QCheckBox("Genetic abnormalities")
        self.genetic_abnormalities_description_input = QTextEdit()
        self.genetic_abnormalities_description_input.setFixedHeight(80)
        self.seizure_epileptic_attack_checkbox = QCheckBox("Seizure or epileptic attack")
        self.gestational_age_input = QLineEdit()
        self.birthweight_input = QLineEdit()
        self.birthlength_input = QLineEdit()
        self.pregnancy_complications_checkbox = QCheckBox("Pregnancy or birth complications")
        self.pregnancy_complications_description_input = QTextEdit()
        self.pregnancy_complications_description_input.setFixedHeight(80)

        form.addRow("General Health", self.general_health_input)
        form.addRow("", self.seen_neurologist_checkbox)
        form.addRow("Neurologist Description", self.neurologist_description_input)
        form.addRow("", self.head_injury_checkbox)
        form.addRow("Head Injury Description", self.head_injury_description_input)
        form.addRow("", self.genetic_abnormalities_checkbox)
        form.addRow("Genetic Abnormalities Description", self.genetic_abnormalities_description_input)
        form.addRow("", self.seizure_epileptic_attack_checkbox)
        form.addRow("Gestational Age", self.gestational_age_input)
        form.addRow("Birthweight", self.birthweight_input)
        form.addRow("Birthlength", self.birthlength_input)
        form.addRow("", self.pregnancy_complications_checkbox)
        form.addRow("Complications Description", self.pregnancy_complications_description_input)

        save_button = QPushButton("Save Medical History")
        save_button.setObjectName("PrimaryButton")
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
        self.seen_neurologist_checkbox.setChecked(bool(data.get("seen_neurologist")))
        self.neurologist_description_input.setPlainText(data.get("neurologist_description") or "")
        self.head_injury_checkbox.setChecked(bool(data.get("head_injury")))
        self.head_injury_description_input.setPlainText(data.get("head_injury_description") or "")
        self.genetic_abnormalities_checkbox.setChecked(bool(data.get("genetic_abnormalities")))
        self.genetic_abnormalities_description_input.setPlainText(
            data.get("genetic_abnormalities_description") or ""
        )
        self.seizure_epileptic_attack_checkbox.setChecked(
            bool(data.get("seizure_epileptic_attack"))
        )
        self.gestational_age_input.setText(data.get("gestational_age") or "")
        self.birthweight_input.setText(data.get("birthweight") or "")
        self.birthlength_input.setText(data.get("birthlength") or "")
        self.pregnancy_complications_checkbox.setChecked(
            bool(data.get("pregnancy_complications"))
        )
        self.pregnancy_complications_description_input.setPlainText(
            data.get("pregnancy_complications_description") or ""
        )

    def collect_data(self) -> dict:
        return {
            "general_health": self.general_health_input.toPlainText().strip(),
            "seen_neurologist": int(self.seen_neurologist_checkbox.isChecked()),
            "neurologist_description": self.neurologist_description_input.toPlainText().strip(),
            "head_injury": int(self.head_injury_checkbox.isChecked()),
            "head_injury_description": self.head_injury_description_input.toPlainText().strip(),
            "genetic_abnormalities": int(self.genetic_abnormalities_checkbox.isChecked()),
            "genetic_abnormalities_description": (
                self.genetic_abnormalities_description_input.toPlainText().strip()
            ),
            "seizure_epileptic_attack": int(self.seizure_epileptic_attack_checkbox.isChecked()),
            "gestational_age": self.gestational_age_input.text().strip(),
            "birthweight": self.birthweight_input.text().strip(),
            "birthlength": self.birthlength_input.text().strip(),
            "pregnancy_complications": int(self.pregnancy_complications_checkbox.isChecked()),
            "pregnancy_complications_description": (
                self.pregnancy_complications_description_input.toPlainText().strip()
            ),
        }

    def save(self) -> None:
        save_medical_history(self.patient_id, self.collect_data())
        QMessageBox.information(self, "Saved", "Medical history saved successfully.")
