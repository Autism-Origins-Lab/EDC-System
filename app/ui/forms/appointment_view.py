from datetime import datetime

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QTextCharFormat
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QDateEdit,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.forms import save_telephone_screening
from app.database.repositories.patients import list_patients
from app.services import preferences
from app.services.slack_reminders import (  # Slack reminders are sent by scripts/send_slack_reminders.py
    REMINDER_MESSAGES,
    parse_date,
)

REMINDER_STATUS = {
    1: "First Reminder Sent!",
    2: "Second Reminder Sent!",
    3: "Final Reminder Sent!",
}


class calendarEffects(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_date = None
        self.cell_rects = {}  # date -> where that day was drawn, filled in by paintCell
        self.view = self.findChild(QtWidgets.QTableView, "qt_calendar_calendarview")
        self.view.viewport().setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.view.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.position().toPoint()
                hovered = next((d for d, r in self.cell_rects.items() if r.contains(pos)), None)
                if hovered != self.hovered_date:
                    self.hovered_date = hovered
                    self.view.viewport().update()
            elif event.type() == QEvent.Leave:
                self.hovered_date = None
                self.view.viewport().update()
        return super().eventFilter(obj, event)

    def paintCell(self, painter: QPainter, rect, date) -> None:
        self.cell_rects[date] = QtCore.QRect(rect)
        super().paintCell(painter, rect, date)  # normal day: text, today/weekend colours, selection
        if date == self.hovered_date and date != self.selectedDate():
            painter.fillRect(rect, QColor(22, 106, 184, 40))  # see-through brand blue


class appointmentView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.patients = []
        self.main_layout = QVBoxLayout(self)
        self.setStyleSheet("QLabel { color: #1f2937; }")

        title_label = QLabel("Appointments")
        title_label.setFont(QFont("Helvetica Neue", 25, QFont.Weight.Bold))
        sub_title_label = QLabel("View and manage appointments for patients.")
        sub_title_font = QFont("Helvetica Neue", 12)
        sub_title_font.setItalic(True)
        sub_title_label.setFont(sub_title_font)

        self.main_layout.addWidget(title_label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(sub_title_label)

        self.appointment_table_list = QTableWidget()
        self.appointment_table_list.cellDoubleClicked.connect(self.change_schedule_date)
        self.appointment_table_list.setColumnCount(7)
        self.appointment_table_list.setHorizontalHeaderLabels(
            ["Subject ID", "Patient Name", "Schedule Date", "Birth Date", "Familial Risk", "Sex", "Reminders Sent"]
        )
        self.appointment_table_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.appointment_table_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.appointment_table_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.appointment_table_list.verticalHeader().setVisible(False)
        self.appointment_table_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointment_table_list.setFont(QFont("Helvetica Neue", 15))
        self.appointment_table_list.viewport().installEventFilter(self)
        self.main_layout.addWidget(self.appointment_table_list, 1)

    def refresh_appointment_list(self):
        now = datetime.now()

        appointments = []
        for patient in list_patients():
            date_str = patient["schedule_date"]
            if not date_str:
                continue
            scheduled = parse_date(date_str)
            if scheduled is None:
                print(f"Unrecognized date for {patient['subject_id']}: {date_str!r}")
                continue
            if scheduled.date() >= now.date():
                appointments.append((scheduled, patient))

        # Bubble sort, earliest appointment first.
        swapped = True
        while swapped:
            swapped = False
            for i in range(len(appointments) - 1):
                if appointments[i][0] > appointments[i + 1][0]:
                    appointments[i], appointments[i + 1] = appointments[i + 1], appointments[i]
                    swapped = True

        self.patients = [patient for _, patient in appointments]

        table = self.appointment_table_list
        table.setRowCount(len(appointments))
        for row, (scheduled, patient) in enumerate(appointments):
            if patient["high_familial_risk"] == 1:
                risk = "High Risk"
            elif patient["low_familial_risk"] == 1:
                risk = "Low Risk"
            else:
                risk = "Not evaluated"

            # The daily job sends a reminder 14, 7 and 1 days before, so count the ones already reached.
            days_until = (scheduled.date() - now.date()).days
            reminder_count = sum(1 for days in REMINDER_MESSAGES if days >= days_until)
            reminder_status = REMINDER_STATUS.get(reminder_count, "No Reminders Sent Yet")

            table.setItem(row, 0, QTableWidgetItem(patient["subject_id"]))
            table.setItem(row, 1, QTableWidgetItem(patient["child_name"] or "Unnamed"))
            table.setItem(row, 2, QTableWidgetItem(scheduled.strftime("%Y-%m-%d")))
            table.setItem(row, 3, QTableWidgetItem(patient["date_of_birth"] or "Unknown"))
            table.setItem(row, 4, QTableWidgetItem(risk))
            table.setItem(row, 5, QTableWidgetItem(patient["sex"] or "Unknown"))
            table.setItem(row, 6, QTableWidgetItem(reminder_status))

    def showEvent(self, event):
        self.refresh_appointment_list()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.clear_list_selection()
        super().mousePressEvent(event)

    def clear_list_selection(self):
        self.appointment_table_list.clearSelection()
        self.appointment_table_list.setCurrentCell(-1, -1)  # Deselect any current cell

    def eventFilter(self, obj, event):
        if (
            obj is self.appointment_table_list.viewport()
            and event.type() == QEvent.MouseButtonPress
            and self.appointment_table_list.itemAt(event.position().toPoint()) is None
        ):
            self.clear_list_selection()
        return super().eventFilter(obj, event)

    def change_schedule_date(self, row: int, column: int):
        patient = self.patients[row]
        date_format = preferences.load_preferences()["date_format"]

        schedule_change_frame = QFrame(self, Qt.Popup)
        schedule_change_frame.setAttribute(Qt.WA_DeleteOnClose)  # don't keep a hidden frame per double-click
        schedule_change_frame.setObjectName("ScheduleChanger")
        schedule_change_frame.setStyleSheet("""
            QFrame#ScheduleChanger {
                background: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)
        schedule_change_frame.setFixedWidth(200)  # height follows the contents

        schedule_change_layout = QVBoxLayout(schedule_change_frame)
        schedule_change_layout.setSpacing(5)
        schedule_change_layout.setContentsMargins(5, 5, 5, 5)
        schedule_change_layout.addWidget(QLabel("Change Schedule Date"))

        schedule_change_input = QDateEdit()
        schedule_change_input.setCalendarPopup(True)
        schedule_change_input.setCalendarWidget(calendarEffects())
        calendar = schedule_change_input.calendarWidget()
        calendar.setStyleSheet("""
            QCalendarWidget QToolButton {
                color: #ffffff;
                background: transparent;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QCalendarWidget QToolButton:hover {
                background: #115492;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            QCalendarWidget QSpinBox {
                color: #1f2937;
                background: #ffffff;
                selection-background-color: #eaf1ff;
                selection-color: #1f2937;
            }
            QCalendarWidget QAbstractItemView {
                background: #ffffff;
                selection-color: #ffffff;
                outline: 0;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #cbd5e1;
            }
        """)
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        calendar.setFirstDayOfWeek(Qt.Sunday)

        for name, arrow in (("qt_calendar_prevmonth", "‹"), ("qt_calendar_nextmonth", "›")):
            button = calendar.findChild(QToolButton, name)
            if button is not None:
                button.setIcon(QIcon())
                button.setText(arrow)

        day_header = QTextCharFormat()
        day_header.setForeground(QColor("#6b7280"))
        day_header.setFontWeight(QFont.Weight.DemiBold)
        calendar.setHeaderTextFormat(day_header)

        weekend = QTextCharFormat()
        weekend.setForeground(QColor("#6b7280"))  # grey instead of Qt's default red
        calendar.setWeekdayTextFormat(Qt.Saturday, weekend)
        calendar.setWeekdayTextFormat(Qt.Sunday, weekend)

        today = QTextCharFormat()
        today.setForeground(QColor("#1d63ed"))
        today.setFontWeight(QFont.Weight.Bold)
        calendar.setDateTextFormat(QDate.currentDate(), today)

        # Show the picker in the same format as the Settings preference.
        schedule_change_input.setDisplayFormat("MM/dd/yyyy" if date_format == "MM/DD/YYYY" else "yyyy-MM-dd")
        schedule_change_input.setDate(QDate.fromString(self.appointment_table_list.item(row, 2).text(), "yyyy-MM-dd"))
        schedule_change_layout.addWidget(schedule_change_input)

        schedule_change_line = QLineEdit()
        schedule_change_line.setPlaceholderText(f"or type a date ({date_format})")
        schedule_change_layout.addWidget(schedule_change_line)

        save_button = QPushButton("Save")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setObjectName("PrimaryButton")
        schedule_change_layout.addWidget(save_button)

        def save() -> None:
            typed_date = schedule_change_line.text().strip()
            if typed_date:  # a typed date wins over the picker
                try:
                    new_date = preferences.parse_date(typed_date, date_format)
                except ValueError as exc:
                    QMessageBox.warning(self, "Unable to save", str(exc))
                    return
            else:
                new_date = schedule_change_input.date().toString("yyyy-MM-dd")

            save_telephone_screening(patient["id"], {"schedule_date": new_date})
            schedule_change_frame.close()
            self.refresh_appointment_list()

        save_button.clicked.connect(save)
        schedule_change_line.returnPressed.connect(save)

        schedule_change_frame.move(QCursor.pos())
        schedule_change_frame.show()
