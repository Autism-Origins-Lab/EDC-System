from PySide6.QtCore import Qt, Signal, Slot, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
    QSizePolicy

)

from app.database.queries.patients import list_patients
from app.ui.views.new_patient_dialog import NewPatientDialog
from app.ui.views.patient_detail_view import PatientDetailView

class DonutChart(QWidget):
    #just draw arcs with QPainter w/ PySide6. no difference in styling
    def __init__(self):
        super().__init__()
        self.segments: list[tuple[str,int,str]] = []
        #label, value, color
        self._center_value: int = 0 #this will be total # of patients
        self.setMinimumSize(140,140)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_segments(self, segments: list[tuple[str,int,str]], center_value: int | None = None) -> None:
            self._segments = segments
            self._center_value = center_value if center_value is not None else sum(v for _, v, _ in segments)
            self.update()

    def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            side = min(self.width(), self.height())
            thickness = side * 0.18
            margin = thickness/2+4
            rect = QRectF(margin, margin, side-2*margin, side-2*margin)


            denom = self._center_value if self._center_value > 0 else sum(value for _, value, _ in self._segments)
            track_pen = QPen(QColor("#1a1a1a"), thickness)
            track_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(track_pen)
            painter.drawArc(rect, 0, 360*16)

            if denom > 0:
                start_angle = 90*16
                for _, value, color in self._segments:
                    if value <= 0:
                        continue
                    span_angle = int(-(value/denom) * 360 * 16)
                    pen = QPen(QColor(color), thickness)
                    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                    painter.setPen(pen)
                    painter.drawArc(rect, start_angle, span_angle)
                    start_angle += span_angle
            painter.setPen(QColor("#1a1a1a"))
            font = QFont(painter.font())
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._center_value))
            painter.end()


class PatientsView(QWidget):
    patient_data_changed = Signal()
    def __init__(self):
        super().__init__()
        self.patients: list[dict] = []
        self.current_sort = "Newest First"

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
        metrics.setSpacing(25)

        self.metrics_donut_chart = DonutChart()
        donut_block = QVBoxLayout()
        donut_block.setSpacing(5)
        donut_caption = QLabel("Total patients")
        donut_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donut_caption.setStyleSheet("color: #666666; font-size: 11px; font-weight: bold;")
        donut_block.addWidget(self.metrics_donut_chart)
        donut_block.addWidget(donut_caption)

        legend = QVBoxLayout()
        legend.setSpacing(10)
        self.pending_forms_row, self.pending_forms_label = self._legend_item(
            "#D00B60", "Pending forms"
        )
        self.ready_exports_row, self.ready_exports_label = self._legend_item(
            "#08AEA9", "Ready exports"
        )

        #this is just a test to see what pending vs complete vs neither would look like.
        self.edge_case_row, self.edge_case_label = self._legend_item(
            "#5C5C5C", "(edge case)"
        )
        legend.addWidget(self.pending_forms_row)
        legend.addWidget(self.ready_exports_row)
        legend.addWidget(self.edge_case_row)
        legend.addStretch()

        metrics.addLayout(donut_block)
        metrics.addLayout(legend)
        metrics.addStretch()


   
        controls = QHBoxLayout()

        filter_button = QPushButton("Filter")
        filter_button.setObjectName("SecondaryButton")
        filter_button.setCursor(Qt.PointingHandCursor)

        filter_menu = QMenu(self)
        filter_menu.addAction("Name (A-Z)", lambda: self.apply_sort("Name (A-Z)"))
        filter_menu.addAction("Name (Z-A)", lambda: self.apply_sort("Name (Z-A)"))
        filter_menu.addAction("Eligibility (Yes First)", lambda: self.apply_sort("Eligibility (Yes First)"))
        filter_menu.addAction("Eligibility (No First)", lambda: self.apply_sort("Eligibility (No First)"))
        filter_menu.addAction("Schedule Date (Earliest First)", lambda: self.apply_sort("Schedule Date (Earliest First)"))
        filter_menu.addAction("Schedule Date (Latest First)", lambda: self.apply_sort("Schedule Date (Latest First)"))
        filter_button.setMenu(filter_menu)

        # Sorting options added to a filter menu

        controls.addWidget(filter_button)

        self.table = QTableWidget()
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Subject ID", "Child Name", "Eligibility", "Screener", "Schedule Date", "Comment"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self.open_patient_detail)
        self.table.viewport().setCursor(Qt.PointingHandCursor)

        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(controls)
        layout.addWidget(self.table, 1)

        self.load_patients()

    def _legend_item(self, color: str, name: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

        text = QLabel(f"{name}: 0")
        text.setStyleSheet("color: #1a1a1a; font-size: 13px;")

        row_layout.addWidget(dot)
        row_layout.addWidget(text)
        row_layout.addStretch()

        text.setProperty("legend_name", name)
        return row, text

    
    def apply_sort(self, sort_choice: str) -> None: #applies the sorting lofic, this need to be applied to the new list returned by the signal in topbar.py
        self.current_sort = sort_choice
        self.load_patients()

    def load_patients(self) -> None: #I removed the table search because patients is sorted via filter menu
        #search is now in topbar's global search..
        patients = list_patients(sort_by=self.current_sort)
        self.update_table(patients)

    @Slot(list)
    def update_table(self, patients: list[dict]) -> None:
        #update table & metrics. TopBar signals
        self.patients = patients
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.patients))

        pending_forms = 0
        completed_forms = 0 # not hardcoded

        for row_index, patient in enumerate(self.patients):
            status = patient.get("form_status", "Pending")
            if status == "Pending": 
                pending_forms += 1
            if status == "Complete": 
                completed_forms += 1

            values = [
                    patient.get("subject_id", "N/A"),
                    patient.get("child_name", "N/A"),
                    patient.get("eligibility", "N/A"),
                    patient.get("screener", "N/A"),
                    patient.get("schedule_date", "N/A"),
                    patient.get("comment", ""),
                ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value) if value is not None else "N/A")
                item.setForeground(Qt.GlobalColor.black)
                item.setData(Qt.UserRole, patient.get("id"))
                self.table.setItem(row_index, column_index, item)
 
    

        other_forms = len(self.patients) - pending_forms - completed_forms

        self.pending_forms_label.setText(f"Pending forms: {pending_forms}")
        self.ready_exports_label.setText(f"Ready exports: {completed_forms}")
        self.edge_case_label.setText(f"(edge case): {other_forms}")

        self.metrics_donut_chart.set_segments(
            [
                ("Pending forms", pending_forms, "#D82454"),
                ("Ready exports", completed_forms, "#44CCAA"),
            ],
            center_value=len(self.patients),
        )

    def open_new_patient_dialog(self) -> None:
        dialog = NewPatientDialog(self)

        if dialog.exec() == NewPatientDialog.DialogCode.Accepted:
            self.load_patients()
            self.patient_data_changed.emit()

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
        self.patient_data_changed.emit()
