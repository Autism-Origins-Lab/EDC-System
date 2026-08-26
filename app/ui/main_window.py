from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.sidebar import Sidebar
from app.ui.topbar import TopBar
from app.ui.views.patients_view import PatientsView

# Export patient data to excel sheet or a patient summary 
# An overview window total number of participants, how many are elgible, 
# Being able to attach the EEG and their corresponding files to their data
# A way to keep the infants age updated based on the time the file has been completed --> change action column
# 

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EDC System")
        self.resize(1280, 760)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        body = QFrame()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.section_selected.connect(self.show_section)

    #Mouse changes on hover for each placeholder page, to make it look clickable.
        for placeholder_page in self.sidebar.findChildren(QWidget):
            placeholder_page.setCursor(Qt.PointingHandCursor)

        self.pages = QStackedWidget()
        self.section_indexes = {
            "Patients": self.pages.addWidget(PatientsView()),
            "Telephone Screening": self.pages.addWidget(
                self._build_placeholder_page(
                    "Telephone Screening",
                    "Open a patient from the Patients page to complete this form.",
                )
            ),
            "Questionnaires": self.pages.addWidget(
                self._build_placeholder_page(
                    "Questionnaires",
                    "Open a patient from the Patients page to complete questionnaires.",
                )
            ),
            "Medical History": self.pages.addWidget(
                self._build_placeholder_page(
                    "Medical History",
                    "Open a patient from the Patients page to complete medical history.",
                )
            ),
            "Family History": self.pages.addWidget(
                self._build_placeholder_page(
                    "Family History",
                    "Open a patient from the Patients page to complete family history.",
                )
            ),
            "Imports": self.pages.addWidget(
                self._build_placeholder_page(
                    "Imports",
                    "Spreadsheet import tools will live here after the core forms are stable.",
                )
            ),
            "Exports": self.pages.addWidget(
                self._build_placeholder_page(
                    "Exports",
                    "Excel export controls will live here when exports are brought into the UI.",
                )
            ),
            "Settings": self.pages.addWidget(
                self._build_placeholder_page(
                    "Settings",
                    "Local database, backup, and app preferences will live here.",
                )
            ),
        }

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages, 1)

        root_layout.addWidget(TopBar())
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

    def show_section(self, section: str) -> None:
        self.pages.setCurrentIndex(self.section_indexes[section])

    def _build_placeholder_page(self, title: str, message: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 18)
        layout.setSpacing(8)
        #labels are inline this way, no need to use local variable declarations
        layout.addWidget(QLabel(title, objectName="PageTitle"))

        body = QLabel(message, objectName="Muted")
        body.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(body)

        layout.addStretch()
        return page
