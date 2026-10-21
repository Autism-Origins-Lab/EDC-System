from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView
)
import os
from PySide6.QtGui import QFont
from PySide6.QtCore import QEvent, Qt
from PySide6.QtCore import QSize
from datetime import datetime
from app.database.repositories.patients import list_patients
from app.services.slack_reminders import REMINDER_MESSAGES, parse_date  # Slack reminders are sent by scripts/send_slack_reminders.py

class appointmentView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.setStyleSheet("QLabel { color: #1f2937; }")
        Title_label = QLabel("Appointments")
        sub_title_label = QLabel("View and manage appointments for patients.")
        title_font = QFont("Helvetica Neue", 25, QFont.Weight.Bold)
        Title_label.setFont(title_font)
        sub_title_font = QFont("Helvetica Neue", 12)
        sub_title_font.setItalic(True)
        sub_title_label.setFont(sub_title_font)

        self.main_layout.addWidget(Title_label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(sub_title_label)

        self.appointment_table_list = QTableWidget()
        self.appointment_table_list.setColumnCount(7)
        self.appointment_table_list.setHorizontalHeaderLabels(
            ["Subject ID", "Patient Name", "Schedule Date", "Birth Date", "Familial Risk", "Sex","Reminders Sent"]
        )
        self.appointment_table_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.appointment_table_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.appointment_table_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.appointment_table_list.verticalHeader().setVisible(False)
        self.appointment_table_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointment_table_list.setFont(QFont("Helvetica Neue", 15))
        self.appointment_table_list.viewport().installEventFilter(self)
        self.main_layout.addWidget(self.appointment_table_list, 1)
        if 
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
            if reminder_count == 1:
                reminder_count = "First Reminder Sent!"
            elif reminder_count == 2:
                reminder_count = "Second Reminder Sent!"
            elif reminder_count == 3:
                reminder_count = "Final Reminder Sent!"
            else:
                reminder_count = "No Reminders Sent Yet"

            table.setItem(row, 0, QTableWidgetItem(patient["subject_id"]))
            table.setItem(row, 1, QTableWidgetItem(patient["child_name"] or "Unnamed"))
            table.setItem(row, 2, QTableWidgetItem(scheduled.strftime("%Y-%m-%d")))
            table.setItem(row, 3, QTableWidgetItem(patient["date_of_birth"] or "Unknown"))
            table.setItem(row, 4, QTableWidgetItem(risk))
            table.setItem(row, 5, QTableWidgetItem(patient["sex"] or "Unknown"))
            table.setItem(row, 6, QTableWidgetItem(str(reminder_count)))

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
        if obj is self.appointment_table_list.viewport() and event.type() == QEvent.MouseButtonPress:
                if self.appointment_table_list.itemAt(event.position().toPoint()) is None:
                    self.clear_list_selection()
        return super().eventFilter(obj, event)

    def change_schedule_date(self, new_date: str):
        selected_items = self.appointment_table_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No patient selected", "Please select a patient first.")
            return

        selected_row = selected_items[0].row()
        patient = self.patients[selected_row]
        patient["schedule_date"] = new_date
        self.refresh_appointment_list()
