from PySide6.QtCore import Qt
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
        new_patient.setObjectName("PrimaryButton")
        new_patient.clicked.connect(self.open_new_patient_dialog)

        header.addLayout(title_block)
        header.addStretch()
        header.addWidget(new_patient)

        metrics = QHBoxLayout()
        self.total_patients_metric = self._metric("Total patients", "0")
        self.pending_forms_metric = self._metric("Pending forms", "0")
        self.ready_exports_metric = self._metric("Ready exports", "0")

        metrics.addWidget(self.total_patients_metric)
        metrics.addWidget(self.pending_forms_metric)
        metrics.addWidget(self.ready_exports_metric)
        metrics.addStretch()

        controls = QHBoxLayout()
        self.table_search = QLineEdit()
        self.table_search.setPlaceholderText("Search patient table")
        self.table_search.textChanged.connect(self.load_patients)

        filter_button = QPushButton("Filter")
        filter_button.setObjectName("SecondaryButton")

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

        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(controls)
        layout.addWidget(self.table, 1)

        self.load_patients()

    def _metric(self, label_text: str, value_text: str) -> QFrame:
        box = QFrame()
        box.setMinimumWidth(180)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 24, 0)

        label = QLabel(label_text)
        label.setObjectName("Muted")

        value = QLabel(value_text)
        value.setObjectName("MetricValue")

        layout.addWidget(label)
        layout.addWidget(value)

        box.value_label = value
        return box

    def load_patients(self) -> None:
        search_text = self.table_search.text()
        self.patients = search_patients(search_text) if search_text.strip() else list_patients()

        self.table.setRowCount(len(self.patients))

        pending_forms = 0

        for row_index, patient in enumerate(self.patients):
            if patient["eligibility"] == "Not started":
                pending_forms += 1

            values = [
                patient["subject_id"],
                patient["child_name"],
                patient["eligibility"],
                patient["screener"],
                patient["schedule_date"],
                "Open",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column_index == 5:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)

        self.total_patients_metric.value_label.setText(str(len(self.patients)))
        self.pending_forms_metric.value_label.setText(str(pending_forms))
        self.ready_exports_metric.value_label.setText("0")

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

    def show_patient_detail(self, patient_id: int) -> None:
        dialog = PatientDetailView(patient_id, self)
        dialog.exec()
        self.load_patients()