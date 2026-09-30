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
    QSizePolicy,
    QButtonGroup

)

from app.database.queries.patients import (
    list_patients,
    FILTER_YES,
    FILTER_NO,
    FILTER_NOT_EVALUATED
)
from app.ui.views.new_patient_dialog import NewPatientDialog
from app.ui.views.patient_detail_view import PatientDetailView

PENDING_COLOR = "#D00B60"
READY_COLOR = "#08AEA9"
EDGE_COLOR = "#5C5C5C"
BLUE_COLOR = "#166AB8"

class DonutChart(QWidget):
    #just draw arcs with QPainter w/ PySide6. no difference in styling
    def __init__(self):
        super().__init__()
        self._segments: list[tuple[str,int,str]] = []
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
        self.current_eligibility_filter: str | None = None
        self.current_search_text = ""

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

        new_patient = QPushButton("+ Patient")
        new_patient.setStyleSheet(self.new_patient_style())
        new_patient.setCursor(Qt.PointingHandCursor)
        new_patient.setObjectName("PrimaryButton")
        new_patient.clicked.connect(self.open_new_patient_dialog)

        header.addLayout(title_block)
        header.addStretch()

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
            PENDING_COLOR, "Pending forms"
        )
        self.ready_exports_row, self.ready_exports_label = self._legend_item(
            READY_COLOR, "Ready exports"
        )

        #this is just a test to see what pending vs complete vs neither would look like.
        self.edge_case_row, self.edge_case_label = self._legend_item(
            EDGE_COLOR, "(edge case)"
        )
        legend.addWidget(self.pending_forms_row)
        legend.addWidget(self.ready_exports_row)
        legend.addWidget(self.edge_case_row)
        legend.addStretch()

        metrics.addLayout(donut_block)
        metrics.addLayout(legend)
        metrics.addStretch()


   
        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(new_patient)

        self.sort_button = QPushButton(f"Sort: {self.current_sort}")
        self.sort_button.setObjectName("SecondaryButton")
        self.sort_button.setCursor(Qt.PointingHandCursor)


        sort_menu = QMenu(self)
        sort_menu.addAction("Name (A-Z)", lambda: self.apply_sort("Name (A-Z)"))
        sort_menu.addAction("Name (Z-A)", lambda: self.apply_sort("Name (Z-A)"))
        sort_menu.addAction("Schedule Date (Earliest First)", lambda: self.apply_sort("Schedule Date (Earliest First)"))
        sort_menu.addAction("Schedule Date (Latest First)", lambda: self.apply_sort("Schedule Date (Latest First)"))
        sort_menu.addAction("Newest First", lambda: self.apply_sort("Newest First"))
        self.sort_button.setMenu(sort_menu)
        controls.addWidget(self.sort_button)

        eligibility_label = QLabel("Eligibility: ")
        eligibility_label.setStyleSheet("font-weight: bold; color: #120713")
        controls.addWidget(eligibility_label)

        self.eligibility_filter_group = QButtonGroup(self)
        self.eligibility_filter_group.setExclusive(True)
        all = QPushButton("All")
        yes = QPushButton("Yes")
        no = QPushButton("No")
        not_eval = QPushButton("Not Evaluated")

        filter_configs = [
            (all, None),
            (yes, FILTER_YES),
            (no, FILTER_NO),
            (not_eval, FILTER_NOT_EVALUATED)
        ]
        self.all = all

        for btn, filter_value in filter_configs:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self.button_style())
            btn.setObjectName("SecondaryButton")
            self.eligibility_filter_group.addButton(btn)
            btn.clicked.connect(lambda _, val=filter_value: self.apply_eligibility_filter(val))
            controls.addWidget(btn)
    
        all.setChecked(True)
        controls.addStretch()

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
        self.table.cellClicked.connect(self.open_patient_detail)
        self.table.viewport().setCursor(Qt.PointingHandCursor)
        self.table.setStyleSheet(self.table_style)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header_view.setHighlightSections(False)

        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(controls)
        layout.addWidget(self.table, 1)

        self.load_patients()

    @staticmethod
    def new_patient_style() -> str:
        return f"""
        QPushButton {{
            background-color: {BLUE_COLOR};
            color: #FFFFFF;
            border-radius: 20px;
            padding: 12px 16px;
        }}
            QPushButton:hover {{
            background-color: #115492;
        }}
        QPushButton:pressed {{
            background-color: #115492;
        }}
        """
    @staticmethod
    def button_style() -> str:
         return """
                 QPushButton:hover {
                    background-color: #F1F5F9;
                }
                QPushButton:pressed {
                    background-color: #F1F5F9;
                }
                """

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

    def set_search_text(self, search_text: str) -> None:
        self.current_search_text = search_text
        self.load_patients()

    def apply_eligibility_filter(self, choice: str | None) -> None:
        self.current_eligibility_filter = choice
        self.load_patients()

    def load_patients(self) -> None:
        patients = list_patients(
            sort_by=self.current_sort,
            eligibility_filter=self.current_eligibility_filter,
        )
        if self.current_search_text:
            patients = self.filter_by_search(patients, self.current_search_text)
        self.update_table(patients)

        print("filter:", self.current_eligibility_filter, "| sort:", self.current_sort) #debugging


    @staticmethod
    def filter_by_search(patients: list[dict], search_text:str) -> list[dict]:
        query = search_text.strip().lower()

        if not query:
            return patients

        filtered: list[dict] = []

        for patient in patients:
            child_name = str(patient.get("child_name") or "").lower()
            subject_id = str(patient.get("subject_id") or "").lower()

            if "," in query:
                parts = [p.strip() for p in query.split(",", 1)]
                name_part = parts[0]
                id_part = parts[1] if len(parts) > 1 else ""

                if name_part in child_name and id_part in subject_id:
                    filtered.append(patient)
            else:
                if query in child_name or query in subject_id:
                    filtered.append(patient)

        return filtered #I want this list to be sent to patients_view to displau the table as needed, when something is searched 
    


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
                    patient.get("eligibility", "Not evaluated"),
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
                ("Pending forms", pending_forms, PENDING_COLOR),
                ("Ready exports", completed_forms, READY_COLOR),
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

    table_style = f""" 
        QTableWidget {{ /*Items in the table */
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            gridline-color: #EDF2F7;
            font-size: 13px;
            color: #1A202C;
            outline: none;
        }}

        QTableWidget::item {{
            padding: 10px 12px;
            border-bottom: 1px solid #EDF2F7;
        }}

        QTableWidget::item:hover {{
            background-color: #F1F5F9;
        }}

        QTableWidget::item:selected {{
            background-color: #913899;
            color: #FFFFFF;
        }}

        QHeaderView::section {{
            background-color: #115492;
            color: #FCFCFD;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            padding: 10px 12px;
            border: none;
            border-bottom: 2px solid #E2E8F0;
            border-right: 1px solid #EDF2F7;
        }}

        QHeaderView::section:last {{
            border-right: none;
        }}

        QScrollBar:vertical {{
            border: none;
            background: #F7FAFC;
            width: 8px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background: #CBD5E0;
            border-radius: 4px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: #A0AEC0;
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        """