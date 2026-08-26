from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import list_procedure_schedules, save_procedure_schedule

PROCEDURES = ("Consents", "Recording", "Neuropsych")


class ProcedureScheduleView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id
        self.rows: dict[str, dict[str, QLineEdit]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        for procedure in PROCEDURES:
            group = QGroupBox(procedure)
            form = QFormLayout(group)
            fields = {
                "procedure_time": QLineEdit(),
                "research_assistant": QLineEdit(),
                "room": QLineEdit(),
            }
            fields["procedure_time"].setPlaceholderText("Example: 9:00 AM")
            form.addRow("Time", fields["procedure_time"])
            form.addRow("Research Assistant", fields["research_assistant"])
            form.addRow("Room", fields["room"])
            self.rows[procedure] = fields
            layout.addWidget(group)

        save_button = QPushButton("Save Procedure Schedule")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save)

        layout.addWidget(save_button)
        layout.addStretch()

        self.load_existing_data()

    def load_existing_data(self) -> None:
        for row in list_procedure_schedules(self.patient_id):
            procedure_name = row["procedure_name"]
            if procedure_name not in self.rows:
                continue

            fields = self.rows[procedure_name]
            fields["procedure_time"].setText(row.get("procedure_time") or "")
            fields["research_assistant"].setText(row.get("research_assistant") or "")
            fields["room"].setText(row.get("room") or "")

    def save(self) -> None:
        for procedure_name, fields in self.rows.items():
            save_procedure_schedule(
                self.patient_id,
                procedure_name,
                {
                    "procedure_time": fields["procedure_time"].text().strip(),
                    "research_assistant": fields["research_assistant"].text().strip(),
                    "room": fields["room"].text().strip(),
                },
            )

        QMessageBox.information(self, "Saved", "Procedure schedule saved successfully.")
