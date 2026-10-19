from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QAbstractItemView
)
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from PySide6.QtGui import QFont
from PySide6.QtCore import QEvent, Qt
from PySide6.QtCore import QSize
from datetime import datetime
from app.database.queries.patients import list_patients


DATE_FMT = ["%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"]  # Adjust this format based on your actual date format in the database

def parse_date(value):
    value = value.strip()
    for fmt in DATE_FMT:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None

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

        self.appointment_list_widget = QListWidget()
        self.appointment_list_widget.setFrameShape(QListWidget.NoFrame)
        self.appointment_list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                border: 1px solid black;
                border-radius: 8px;
                padding: 10px;
                margin: 4px 0px;
                background: white;
                color: #1f2937;
            }
            QListWidget::item:hover {
                background: #e5e7eb;
            }
            QListWidget::item:selected {
                background: #dbeafe;
                border: 1px solid black;
                color: #1f2937;
            }
        """)
        self.appointment_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.appointment_list_widget.viewport().installEventFilter(self)
        self.main_layout.addWidget(self.appointment_list_widget)
        self.refresh_appointment_list()

    def refresh_appointment_list(self):
        global date_str
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
                global days_a, days_b
                days_a = (appointments[i][0].date() - now.date()).days
                days_b = (appointments[i + 1][0].date() - now.date()).days
                if days_a > days_b:
                    appointments[i], appointments[i + 1] = appointments[i + 1], appointments[i]
                    swapped = True

        date_str = appointments[0][0].strftime("%Y-%m-%d") if appointments else None
        self.patients = [patient for _, patient in appointments]

        for scheduled, patient in appointments:
            text = f"{scheduled:%a %b %d, %Y}  —  {patient['subject_id']}"
            print(text)
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, patient["subject_id"])
            self.appointment_list_widget.addItem(item)
            self.appointment_list_widget.setSpacing(5)
            self.appointment_list_widget.setFont(QFont("Helvetica Neue", 15))

    def mousePressEvent(self, event):              
        self.clear_list_selection()
        super().mousePressEvent(event)

    def clear_list_selection(self):
        self.appointment_list_widget.clearSelection()
        self.appointment_list_widget.setCurrentRow(-1)

    def eventFilter(self, obj, event):            
        if obj is self.appointment_list_widget.viewport() and event.type() == QEvent.MouseButtonPress:
            if self.appointment_list_widget.itemAt(event.position().toPoint()) is None:
                self.clear_list_selection()
        return super().eventFilter(obj, event)

    def slack_reminder(self, patient_id):
        if not slack_token:
            print("SLACK_BOT_TOKEN is not set. Cannot send Slack message.")
            return

        if days_a == 14 and days_b == 14:
            message = f"Reminder: Patient {patient_id} has an appointment in 14 days."
        elif days_a == 7 and days_b == 7:
            message = f"Reminder: Patient {patient_id} has an appointment in 7 days."
        elif days_a == 1 and days_b == 1:
            message = f"Reminder: Patient {patient_id} has an appointment tomorrow."
        else:
            return

        try:
            response = client.chat_postMessage(
                channel="#general",
                text=message
            )
            print(f"Slack message sent: {response['ts']}")
        except SlackApiError as e:
            print(f"Error sending Slack message: {e.response['error']}")
            

    




