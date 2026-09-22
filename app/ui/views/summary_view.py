from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
)

from app.database.queries.patients import list_patients
from app.database.queries.patient_pdf_export import build_patient_pdf


class PatientExportView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(QLabel("Select a patient to export their record:"))

        self.patient_dropdown = QComboBox()
        self.main_layout.addWidget(self.patient_dropdown)

        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.main_layout.addWidget(self.export_button)

        self.main_layout.addStretch()

        self.refresh_patient_list()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_patient_list()

    def refresh_patient_list(self) -> None:
        self.patient_dropdown.clear()
        self.patients = list_patients()

        for patient in self.patients:
            label = f"{patient['subject_id']} — {patient['child_name'] or 'Unnamed'}"
            self.patient_dropdown.addItem(label)

    def _on_export_clicked(self) -> None:
        index = self.patient_dropdown.currentIndex()
        if index < 0 or not self.patients:
            QMessageBox.warning(self, "No patient selected", "Please select a patient first.")
            return

        patient = self.patients[index]
        default_name = f"{patient['subject_id']}_report.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save patient report", default_name, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            build_patient_pdf(patient["id"], file_path)
            QMessageBox.information(self, "Export complete", f"Saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))