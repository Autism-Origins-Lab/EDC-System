from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.database.queries.patients import create_patient


class NewPatientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Patient")
        self.setModal(True)
        self.created_patient_id: int | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.subject_id_input = QLineEdit()
        self.subject_id_input.setPlaceholderText("Enter subject ID")

        form.addRow("Subject ID", self.subject_id_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.create_patient)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def create_patient(self) -> None:
        try:
            self.created_patient_id = create_patient(self.subject_id_input.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot Create Patient", str(exc))
            return

        self.accept()