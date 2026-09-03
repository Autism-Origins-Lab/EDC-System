from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.patients import list_patients, search_patients
from app.ui.views.new_patient_dialog import NewPatientDialog
from app.ui.views.patient_detail_view import PatientDetailView


class PatientsView(QWidget):
    def __init__(self):
        super().__init__()
        self.patients: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 18)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()

        title = QLabel("Patients")
        title.setObjectName("PageTitle")

        subtitle = QLabel("View patient records, form progress, and scheduled follow-ups.")
        subtitle.setObjectName("Muted")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        new_patient = QPushButton("New Patient")
        new_patient.setCursor(Qt.PointingHandCursor)
        new_patient.setObjectName("PrimaryButton")
        new_patient.clicked.connect(self.open_new_patient_dialog)

        header.addLayout(title_block)
        header.addStretch()
        header.addWidget(new_patient)
#change view -> visuals
        metrics = QHBoxLayout()
        metrics.setSpacing(20)
        self.total_patients_metric = self._metric("Total patients", "0", "#5243FA")
        self.pending_forms_metric = self._metric("Pending forms", "0", "#E32929")
        self.ready_exports_metric = self._metric("Ready exports", "0", "#41A350")

        metrics.addWidget(self.total_patients_metric,1)
        metrics.addWidget(self.pending_forms_metric,1)
        metrics.addWidget(self.ready_exports_metric,1)
        metrics.addStretch()

        controls = QHBoxLayout()
        self.table_search = QLineEdit()
        self.table_search.setPlaceholderText("Search patient table")
        self.table_search.textChanged.connect(self.load_patients)

        filter_button = QPushButton("Filter")
        filter_button.setObjectName("SecondaryButton")
        filter_button.setCursor(Qt.PointingHandCursor)

        controls.addWidget(self.table_search, 1)
        controls.addWidget(filter_button)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Subject ID", "Child Name", "Eligibility", "Screener", "Schedule Date", "Actions"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self.open_patient_detail)
        self.table_search.setCursor(Qt.IBeamCursor)
        self.table.viewport().setCursor(Qt.PointingHandCursor)

        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(controls)
        layout.addWidget(self.table, 1)

        self.load_patients()

    def _metric(self, label_text: str, value_text: str, accent_color: str) -> QFrame:
        box = QFrame()
        box.setObjectName("MetricCard")
        box.setMinimumWidth(180)
        box.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-left: 6px solid {accent_color};
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text.upper())
        label.setStyleSheet("color: #666666; font-size: 11px; font-weight: bold; border: none;")

        value = QLabel(value_text)
        value.setStyleSheet("color: #1a1a1a; font-size: 26px; font-weight: bold; border: none;")

        layout.addWidget(label)
        layout.addWidget(value)

        box.value_label = value
        return box

    def load_patients(self) -> None:
        search_text = self.table_search.text()
        self.patients = search_patients(search_text) if search_text.strip() else list_patients()

        self.table.setRowCount(len(self.patients))

        pending_forms = 0
        completed_forms = 0 #not hardcoded

        for row_index, patient in enumerate(self.patients):
            if patient["eligibility"] == "Not started":
                pending_forms += 1

        

            values = [
                    patient.get("subject_id", "N/A"),
                    patient.get("child_name", "N/A"),
                    patient.get("eligibility", "N/A"),
                    patient.get("screener", "N/A"),
                    patient.get("schedule_date", "N/A"),
                    "Open",
                ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setForeground(Qt.GlobalColor.black)
                
                if column_index == 5:
                    item.setTextAlignment(Qt.AlignCenter)
                
                self.table.setItem(row_index, column_index, item)

        self.total_patients_metric.value_label.setText(str(len(self.patients)))
        self.pending_forms_metric.value_label.setText(str(pending_forms)) #will update this, decrease by one when manual review (mark complete) button is pressed
        self.ready_exports_metric.value_label.setText(str(completed_forms)) #will update this, when manual review is complete by 1.

    def open_new_patient_dialog(self) -> None:
        dialog = NewPatientDialog(self)

        if dialog.exec() == NewPatientDialog.DialogCode.Accepted:
            self.load_patients()

            if dialog.created_patient_id is not None:
                self.show_patient_detail(dialog.created_patient_id)

    def open_patient_detail(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self.patients):
            return

        self.show_patient_detail(self.patients[row]["id"])

    def get_enrollment(self, patient_id: int): #helper function to get enrollment status
         search_text = self.table_search.text()
         self.patients = search_patients(search_text) if search_text.strip() else list_patients()
        
         self.table.setRowCount(len(self.patients))
        
         for row, patient in enumerate(self.patients):
              if patient["subject_id"] == patient_id:
                 return patient["eligibility"] #returns the eligibility status of a patient 

    def set_enrollment_complete(self, patient_id: int):
        enrollment = get_enrollment(patient_id)
        if enrollment != "Eligible":
             search_text = self.table_search.text()
             self.patients = search_patients(search_text) if search_text.strip() else list_patients()
             self.table.setRowCount(len(self.patients))
            
             for row, patient in enumerate(self.patients):
                  if patient["subject_id"] == patient_id:
                    patient["eligibility"] = "Eligible" #changes the eligibility to completed.
            



    def show_patient_detail(self, patient_id: int) -> None:
        dialog = PatientDetailView(patient_id, self)
        dialog.exec()
        self.load_patients()