
from pathlib import Path
import subprocess
import os
import sys
import tempfile
from urllib.parse import quote


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QUrl
from PySide6.QtCore import QSize
from PySide6.QtGui import QDesktopServices, QIcon

from app.database.queries.patients import list_patients
from app.database.queries.patient_pdf_export import build_patient_pdf

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

def _icon(name: str) -> QIcon:
        return QIcon(str(ASSETS_DIR / name))

def _header(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Muted")
    return label

RISK_KEY = "familial_risk"  # replace with the real column name, see below

FILTER_MODES = {
    "eligibility": {
        "key": "eligibility", "match": "yes",
        "left": "Eligible", "right": "Ineligible",
        "button": "Filter by familial risk",
    },
    "risk": {
        "key": RISK_KEY, "match": "high",
        "left": "High risk", "right": "Low risk",
        "button": "Filter by eligibility",
    },
}

class PatientExportView(QWidget):
    
    def __init__(self) -> None:
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.filter_mode = "eligibility"

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Select a patient to export their record:"))
        top_bar.addStretch()
        self.filter_button = QPushButton()
        self.filter_button.clicked.connect(self._toggle_filter)
        top_bar.addWidget(self.filter_button)
        self.main_layout.addLayout(top_bar)

        columns_layout = QHBoxLayout()

        eligible_column = QVBoxLayout()
        self.eligible_header = _header("Eligible")
        eligible_column.addWidget(self.eligible_header)
        self.eligible_list = QListWidget()
        self.eligible_list.setSelectionMode(QAbstractItemView.SingleSelection)
        eligible_column.addWidget(self.eligible_list)
        columns_layout.addLayout(eligible_column)

        ineligible_column = QVBoxLayout()
        self.ineligible_header = _header("Ineligible")
        ineligible_column.addWidget(self.ineligible_header)
        self.ineligible_list = QListWidget()
        self.ineligible_list.setSelectionMode(QAbstractItemView.SingleSelection)
        ineligible_column.addWidget(self.ineligible_list)
        columns_layout.addLayout(ineligible_column)

        self.main_layout.addLayout(columns_layout)

        # selecting in one list clears the other, so only one patient can be picked at a time
        self.eligible_list.itemSelectionChanged.connect(self._on_eligible_selected)
        self.ineligible_list.itemSelectionChanged.connect(self._on_ineligible_selected)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self._on_print_clicked)
        self.main_layout.addWidget(self.print_button)
        self.print_button.setIcon(_icon("printbutton.png"))
        self.print_button.setIconSize(QSize(20, 20))


        self.email_button = QPushButton("Email")
        self.email_button.clicked.connect(self._on_email_clicked)
        self.main_layout.addWidget(self.email_button)
        self.email_button.setIcon(_icon("emailbutton.png"))
        self.email_button.setIconSize(QSize(20, 20))

        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.main_layout.addWidget(self.export_button)
        self.export_button.setIcon(_icon("exportbutton.png"))
        self.export_button.setIconSize(QSize(20, 20))

        self.refresh_patient_list()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_patient_list()

    def refresh_patient_list(self) -> None:
        mode = FILTER_MODES[self.filter_mode]
        self.eligible_header.setText(mode["left"])
        self.ineligible_header.setText(mode["right"])
        self.filter_button.setText(mode["button"])

        self.eligible_list.clear()
        self.ineligible_list.clear()
        self.patients = list_patients()

        for patient in self.patients:
            value = str(patient.get(mode["key"]) or "").strip().lower()
            label = f"{patient['subject_id']} — {patient['child_name'] or 'Unnamed'}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, patient)

            if value == mode["match"]:
                self.eligible_list.addItem(item)
            else:
                self.ineligible_list.addItem(item)

    def _toggle_filter(self) -> None:
        self.filter_mode = "risk" if self.filter_mode == "eligibility" else "eligibility"
        self.refresh_patient_list()

    def _on_eligible_selected(self) -> None:
        if self.eligible_list.selectedItems():
            self.ineligible_list.clearSelection()

    def _on_ineligible_selected(self) -> None:
        if self.ineligible_list.selectedItems():
            self.eligible_list.clearSelection()

    def _selected_patient(self):
        selected = self.eligible_list.selectedItems() or self.ineligible_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No patient selected", "Please select a patient first.")
            return None
        return selected[0].data(Qt.UserRole)

    def _build_temp_pdf(self, patient) -> Path:
        path = Path(tempfile.gettempdir()) / f"{patient['subject_id']}_report.pdf"
        build_patient_pdf(patient["id"], path)
        return path

    def _on_print_clicked(self) -> None:
        patient = self._selected_patient()
        if not patient:
            return

        try:
            path = self._build_temp_pdf(patient)
            if sys.platform.startswith("win"):
                os.startfile(str(path), "print")
            else:  # macOS / Linux
                subprocess.run(["lp", str(path)], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Print failed", str(e))

    def _on_email_clicked(self) -> None:
        patient = self._selected_patient()
        if not patient:
            return

        try:
            path = self._build_temp_pdf(patient)

            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(path)])
            elif sys.platform.startswith("win"):
                subprocess.run(["explorer", "/select,", str(path)])
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

            subject = quote(f"Patient report {patient['subject_id']}")
            QDesktopServices.openUrl(QUrl(f"mailto:?subject={subject}"))
        except Exception as e:
            QMessageBox.critical(self, "Email failed", str(e))

    def _on_export_clicked(self) -> None:
        selected = self.eligible_list.selectedItems() or self.ineligible_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No patient selected", "Please select a patient first.")
            return

        patient = selected[0].data(Qt.UserRole)
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