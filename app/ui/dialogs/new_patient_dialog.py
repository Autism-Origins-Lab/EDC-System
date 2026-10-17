from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.database.repositories.patients import create_patient
from app.services.preferences import load_preferences
from app.ui.theme import (
    DARK_NEW_PATIENT_DIALOG_STYLESHEET,
    NEW_PATIENT_DIALOG_STYLESHEET,
    themed_stylesheet,
)


class NewPatientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NewPatientDialog")
        self.setWindowTitle("New Patient")
        self.setModal(True)
        self.setMinimumSize(520, 300)
        self.resize(560, 320)
        theme = load_preferences()["theme"]
        self.setStyleSheet(
            themed_stylesheet(
                NEW_PATIENT_DIALOG_STYLESHEET,
                DARK_NEW_PATIENT_DIALOG_STYLESHEET,
                theme,
            )
        )
        self.created_patient_id: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        title = QLabel("Create a new patient")
        title.setObjectName("NewPatientTitle")

        subtitle = QLabel(
            "Start a patient workspace with a unique subject ID. "
            "Additional details can be added after creation."
        )
        subtitle.setObjectName("NewPatientSubtitle")
        subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.setSpacing(6)
        header.addWidget(title)
        header.addWidget(subtitle)

        participant_group = QGroupBox("Participant")
        form = QFormLayout(participant_group)
        form.setContentsMargins(24, 30, 24, 24)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.subject_id_input = QLineEdit()
        self.subject_id_input.setObjectName("NewPatientSubjectId")
        self.subject_id_input.setPlaceholderText("e.g. EXAMPLE-001")
        self.subject_id_input.setClearButtonEnabled(True)

        form.addRow("Subject ID", self.subject_id_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        self.create_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.create_button.setText("Create patient")
        self.create_button.setObjectName("NewPatientCreate")
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.cancel_button.setObjectName("NewPatientCancel")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.button_box.accepted.connect(self.create_patient)
        self.button_box.rejected.connect(self.reject)

        layout.addLayout(header)
        layout.addWidget(participant_group)
        layout.addStretch()
        layout.addWidget(self.button_box)

        self.subject_id_input.setFocus()

    def create_patient(self) -> None:
        try:
            self.created_patient_id = create_patient(self.subject_id_input.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot Create Patient", str(exc))
            return

        self.accept()
