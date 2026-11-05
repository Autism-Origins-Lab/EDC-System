from PySide6.QtCore import QEvent, Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.patients import (
    FILTER_NO,
    FILTER_NOT_EVALUATED,
    FILTER_HIGH_RISK,
    FILTER_LOW_RISK,
    FILTER_NOT_EVALUATED_RISK,
    FILTER_YES,
    export_patients_to_csv,
    list_patients,
)
from app.services.preferences import format_date, load_preferences
from app.ui.components.donut_chart import (
    DONUT_EDGE_COLOR,
    DONUT_PENDING_COLOR,
    DONUT_READY_COLOR,
    DonutChart,
)
from app.ui.components.monthly_activity_chart import MonthlyActivityChart
from app.ui.components.risk_bar_chart import RiskBarChart
from app.ui.dialogs.new_patient_dialog import NewPatientDialog
from app.ui.dialogs.patient_detail_view import PatientDetailView
from app.ui.theme import (
    DARK_PATIENTS_TABLE_STYLESHEET,
    PATIENTS_DONUT_CAPTION_STYLESHEET,
    PATIENTS_ELIGIBILITY_LABEL_STYLESHEET,
    PATIENTS_FILTER_BUTTON_STYLESHEET,
    PATIENTS_LEGEND_TEXT_STYLESHEET,
    PATIENTS_NEW_PATIENT_BUTTON_STYLESHEET,
    PATIENTS_PAGE_SCROLL_STYLESHEET,
    PATIENTS_TABLE_ITEM_COLOR,
    PATIENTS_TABLE_STYLESHEET,
    patients_legend_dot_stylesheet,
    themed_stylesheet,
)


RISK_CHART_GAP = 40


class PatientsView(QWidget):
    patient_data_changed = Signal()
    def __init__(self, preferences: dict | None = None):
        super().__init__()
        self.setObjectName("PatientsView")
        self.preferences = preferences or load_preferences()
        self.patients: list[dict] = []

        self.current_sort = "Newest First"
        self.current_risk_filter: str | None = None
        self.current_eligibility_filter: str | None = None
        self.current_search_text = ""

        # The whole page scrolls as one; the table grows to fit its rows instead of scrolling itself.
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("PatientsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(PATIENTS_PAGE_SCROLL_STYLESHEET)
        self.scroll_area.viewport().setAutoFillBackground(False)
        content = QWidget()
        content.setObjectName("PatientsContent")
        self.scroll_area.setWidget(content)
        page_layout.addWidget(self.scroll_area)

        layout = QVBoxLayout(content)
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
        new_patient.setStyleSheet(PATIENTS_NEW_PATIENT_BUTTON_STYLESHEET)
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
        self.donut_caption = QLabel("Total patients")
        self.donut_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.donut_caption.setStyleSheet(PATIENTS_DONUT_CAPTION_STYLESHEET)
        donut_block.addWidget(self.metrics_donut_chart)
        donut_block.addWidget(self.donut_caption)

        legend = QVBoxLayout()
        legend.setSpacing(10)
        self.pending_forms_row, self.pending_forms_label = self._legend_item(
            DONUT_PENDING_COLOR, "Pending forms"
        )
        self.ready_exports_row, self.ready_exports_label = self._legend_item(
            DONUT_READY_COLOR, "Ready exports"
        )

        #this is just a test to see what pending vs complete vs neither would look like.
        self.edge_case_row, self.edge_case_label = self._legend_item(
            DONUT_EDGE_COLOR, "(edge case)"
        )
        
        legend.addWidget(self.pending_forms_row)
        legend.addWidget(self.ready_exports_row)
        legend.addWidget(self.edge_case_row)
        legend.addStretch()

        # Risk breakdown sits beside the donut with the same caption style, so
        # the two summaries read as one row of metrics.
        self.risk_bar_chart = RiskBarChart()
        risk_block = QVBoxLayout()
        risk_block.setSpacing(5)
        risk_block.addWidget(self.risk_bar_chart)
        self.risk_caption = QLabel("Familial risk")
        self.risk_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.risk_caption.setStyleSheet(PATIENTS_DONUT_CAPTION_STYLESHEET)
        risk_block.addWidget(self.risk_caption)

        # The legend and bar chart share their own row so RISK_CHART_GAP is the
        # exact gap between them, independent of the donut's spacing.
        legend_and_risk = QHBoxLayout()
        legend_and_risk.setSpacing(RISK_CHART_GAP)
        legend_and_risk.addLayout(legend)
        legend_and_risk.addLayout(risk_block)

        # Monthly trend of screenings and new high/low risk patients, captioned
        # like the other two charts.
        self.monthly_chart = MonthlyActivityChart()
        monthly_block = QVBoxLayout()
        monthly_block.setSpacing(5)
        monthly_block.addWidget(self.monthly_chart)
        self.monthly_caption = QLabel("Monthly activity")
        self.monthly_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monthly_caption.setStyleSheet(PATIENTS_DONUT_CAPTION_STYLESHEET)
        monthly_block.addWidget(self.monthly_caption)

        metrics.addLayout(donut_block)
        metrics.addLayout(legend_and_risk)
        metrics.addLayout(monthly_block)
        # Stretch factor 1 sends all spare width to the right edge. Without it
        # the legend rows (which contain their own stretch) widen to soak up
        # that space, pushing the bar chart far away from the legend.
        metrics.addStretch(1)

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

        all_btn = QPushButton("All")
        all_btn.setCursor(Qt.PointingHandCursor)
        all_btn.setObjectName("SecondaryButton")
        all_btn.setStyleSheet(PATIENTS_FILTER_BUTTON_STYLESHEET)
        all_btn.clicked.connect(self.clear_filters)
        controls.addWidget(all_btn)
        self.all_btn = all_btn
        self.eligibility_label = QLabel("Status: ")
        self.eligibility_label.setStyleSheet(PATIENTS_ELIGIBILITY_LABEL_STYLESHEET)
        controls.addWidget(self.eligibility_label)

        self.eligibility_filter_group = QButtonGroup(self)
        self.eligibility_filter_group.setExclusive(False)
        yes = QPushButton("Eligible")
        no = QPushButton("Ineligible")
        not_eval = QPushButton("Not Evaluated")

        self.risk_filter_group = QButtonGroup(self)
        self.risk_filter_group.setExclusive(False)
        high = QPushButton("High Risk")
        low = QPushButton("Low Risk")
        noRisk = QPushButton("Unknown Risk")

        risk_filter_configs = [
            (high, FILTER_HIGH_RISK),
            (low, FILTER_LOW_RISK),
            (noRisk, FILTER_NOT_EVALUATED_RISK)
        ]

        eligibility_filter_configs = [
            (yes, FILTER_YES),
            (no, FILTER_NO),
            (not_eval, FILTER_NOT_EVALUATED)
        ]

        for btn, filter_value in eligibility_filter_configs:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(PATIENTS_FILTER_BUTTON_STYLESHEET)
            btn.setObjectName("SecondaryButton")
            self.eligibility_filter_group.addButton(btn)
            btn.clicked.connect(lambda checked, b=btn, val=filter_value: self.apply_eligibility_filter(b, val, checked))
            controls.addWidget(btn)

        self.risk_label = QLabel("Risk: ")
        self.risk_label.setStyleSheet(PATIENTS_ELIGIBILITY_LABEL_STYLESHEET)
        controls.addWidget(self.risk_label)

        for btn, filter_value in risk_filter_configs:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(PATIENTS_FILTER_BUTTON_STYLESHEET)
            btn.setObjectName("SecondaryButton")
            self.risk_filter_group.addButton(btn)
            btn.clicked.connect(lambda checked, b=btn, val=filter_value: self.apply_risk_filter(b, val, checked))
            controls.addWidget(btn)
    
        controls.addStretch()
        export_csv_button = QPushButton("Export CSV")
        export_csv_button.setObjectName("SecondaryButton")
        export_csv_button.setCursor(Qt.PointingHandCursor)
        export_csv_button.clicked.connect(self.export_patients_to_csv)
        
        # Sorting options added to a filter menu
        controls.addWidget(export_csv_button)

        self.table = QTableWidget()
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Subject ID", "Child Name", "Eligibility", "Screener", "Schedule Date", "Comment"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.viewport().installEventFilter(self)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellClicked.connect(self.open_patient_detail)
        self.table.viewport().setCursor(Qt.PointingHandCursor)
        self.table.setStyleSheet(PATIENTS_TABLE_STYLESHEET)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header_view.setHighlightSections(False)

        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(controls)
        layout.addWidget(self.table)
        layout.addStretch()
        # Keep the page's minimum width, as before it was wrapped in a scroll area.
        self.scroll_area.setMinimumWidth(
            content.minimumSizeHint().width() + self.scroll_area.verticalScrollBar().sizeHint().width()
        )

        self.apply_preferences(self.preferences, refresh=False)
        self.load_patients()

    def apply_preferences(self, preferences: dict, *, refresh: bool = True) -> None:
        self.preferences = preferences.copy()
        dark = preferences["theme"] == "Dark"
        self.metrics_donut_chart.set_theme(preferences["theme"])
        self.risk_bar_chart.set_theme(preferences["theme"])
        self.monthly_chart.set_theme(preferences["theme"])
        self.table.setStyleSheet(
            themed_stylesheet(
                PATIENTS_TABLE_STYLESHEET,
                DARK_PATIENTS_TABLE_STYLESHEET,
                preferences["theme"],
            )
        )
        self.table.verticalHeader().setDefaultSectionSize(34)
        text_color = "#e5e7eb" if dark else "#1a1a1a"
        for caption in (self.donut_caption, self.risk_caption, self.monthly_caption):
            caption.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: bold;")
        for label in (self.eligibility_label, self.risk_label):
            label.setStyleSheet(f"font-weight: bold; color: {text_color};")
        for label in (
            self.pending_forms_label,
            self.ready_exports_label,
            self.edge_case_label,
        ):
            label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        if refresh and self.patients:
            self.update_table(self.patients)
        self._fit_table_to_rows()

    def eventFilter(self, watched, event) -> bool:
        # Wheel over the table scrolls the page, since the table itself no longer scrolls.
        if watched is self.table.viewport() and event.type() == QEvent.Type.Wheel:
            QApplication.sendEvent(self.scroll_area.verticalScrollBar(), event)
            return True
        return super().eventFilter(watched, event)

    def _fit_table_to_rows(self) -> None:
        # Show every row so mouse-wheel scrolling over the table moves the page.
        header_height = self.table.horizontalHeader().sizeHint().height()
        rows_height = self.table.verticalHeader().length()
        self.table.setFixedHeight(header_height + rows_height + 2 * self.table.frameWidth())

    def _legend_item(self, color: str, name: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(patients_legend_dot_stylesheet(color))

        text = QLabel(f"{name}: 0")
        text.setStyleSheet(PATIENTS_LEGEND_TEXT_STYLESHEET)

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

    def toggle_in_group(self, group: QButtonGroup, clicked_btn: QPushButton, checked: bool) -> bool:
        if checked:
            for b in group.buttons():
                if b is not clicked_btn:
                    b.setChecked(False)
        return checked

    def apply_eligibility_filter(self, btn, choice: str | None, checked: bool) -> None:
        active = self.toggle_in_group(self.eligibility_filter_group, btn, checked)
        self.current_eligibility_filter = choice if active else None
        self.load_patients()

    def clear_filters(self) -> None:
        self.current_eligibility_filter = None
        self.current_risk_filter = None
        for group in (self.eligibility_filter_group, self.risk_filter_group):
            for b in group.buttons():
                b.setChecked(False)
        self.load_patients()


    def apply_risk_filter(self, btn, choice: str | None, checked: bool) -> None:
           active = self.toggle_in_group(self.risk_filter_group, btn, checked)
           self.current_risk_filter = choice if active else None
           self.load_patients()

    def load_patients(self) -> None:
        patients = list_patients(
            sort_by=self.current_sort,
            eligibility_filter=self.current_eligibility_filter,
            risk_filter=self.current_risk_filter
        )
        if self.current_search_text:
            patients = self.filter_by_search(patients, self.current_search_text)
        self.update_table(patients)

        # print("filters:", self.current_eligibility_filter, " ", self.current_risk_filter, "| sort:", self.current_sort) #debugging


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
            elif status == "Complete": 
                completed_forms += 1

            values = [
                    patient.get("subject_id") or "N/A",
                    patient.get("child_name") or "N/A",
                    patient.get("eligibility") or "Problem with eligibility",
                    patient.get("screener") or "N/A",
                    format_date(patient.get("schedule_date")) or "N/A",
                    patient.get("comment") or "",
                ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setForeground(
                    QColor(
                        "#e5e7eb"
                        if self.preferences["theme"] == "Dark"
                        else PATIENTS_TABLE_ITEM_COLOR
                    )
                )
                item.setData(Qt.UserRole, patient.get("id"))
                self.table.setItem(row_index, column_index, item)
        self._fit_table_to_rows()
 
    

        other_forms = len(self.patients) - pending_forms - completed_forms

        self.pending_forms_label.setText(f"Pending forms: {pending_forms}")
        self.ready_exports_label.setText(f"Ready exports: {completed_forms}")
        self.edge_case_label.setText(f"(edge case): {other_forms}")

        self.metrics_donut_chart.set_segments(
            [
                ("Pending forms", pending_forms, DONUT_PENDING_COLOR),
                ("Ready exports", completed_forms, DONUT_READY_COLOR),
            ],
            center_value=len(self.patients),
        )
        # Same patient list as the donut and table, so all three always agree.
        self.risk_bar_chart.set_patients(self.patients)
        self.monthly_chart.set_patients(self.patients)
        

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
        dialog = PatientDetailView(patient_id, self, self.preferences)
        dialog.exec()
        self.load_patients()
        self.patient_data_changed.emit()

    def export_patients_to_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Patients List to CSV",
            "untitled.csv",
            "CSV Files (*.csv)",
        )
    
        if file_path:
            try:
                export_patients_to_csv(file_path, self.patients)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Patients exported to {file_path}",
                )
            except (OSError, ValueError) as exc:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"An error occurred while exporting patients list: {exc}",
                )
