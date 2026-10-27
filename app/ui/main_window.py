from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.backups import get_backup_manager
from app.services.preferences import load_preferences
from app.ui.components.sidebar import Sidebar
from app.ui.components.topbar import TopBar
from app.ui.pages.patients_view import PatientsView
from app.ui.pages.settings_view import SettingsView
from app.ui.theme import application_stylesheet


class MainWindow(QMainWindow):
    def __init__(self, preferences: dict | None = None) -> None:
        super().__init__()
        self.preferences = preferences or load_preferences()
        self.setWindowTitle("Autism Origins Lab Database")
        self.resize(1280, 760)

        root = QWidget()
        root.setObjectName("ApplicationRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.topbar = TopBar()
        self.sidebar = Sidebar()
        self.patients_view = PatientsView(self.preferences)
        self.settings_view = SettingsView(self.preferences)

        body = QFrame()
        body.setObjectName("ApplicationBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar_expanded = True
        self.sidebar_animation = QPropertyAnimation(self.sidebar,b"maximumWidth")
        self.sidebar_animation.setDuration(250)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.sidebar.section_selected.connect(self.show_section)

        for placeholder_page in self.sidebar.findChildren(QWidget):
            placeholder_page.setCursor(Qt.PointingHandCursor)
 
        self.topbar.search_changed.connect(self.patients_view.set_search_text)

        self.pages = QStackedWidget()
        self.pages.setObjectName("ApplicationPages")
        self.section_indexes = {
            "Patients": self.pages.addWidget(self.patients_view),
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
                self.settings_view
            ),
            
        }

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages, 1)

        self.topbar.menu_clicked.connect(self.toggle_sidebar)
        self.settings_view.preferences_saved.connect(self.apply_preferences)
        self.settings_view.database_restored.connect(self.patients_view.load_patients)
        self.backup_status_timer = QTimer(self)
        self.backup_status_timer.timeout.connect(self.update_backup_status)
        self.backup_status_timer.start(1000)

        root_layout.addWidget(self.topbar)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        self.sidebar.select_section(self.preferences["startup_page"])

    def update_backup_status(self) -> None:
        error = get_backup_manager().last_error
        self.statusBar().showMessage(
            f"Changes saved. Automatic backup failed: {error} Open Settings to retry."
            if error else ""
        )

    def toggle_sidebar(self) -> None:
        collapsed_width = 0
        expanded_width = 280

        self.sidebar_animation.stop()
        self.sidebar_animation.setStartValue(self.sidebar.width())

        if self.sidebar_expanded:
            self.sidebar_animation.setEndValue(collapsed_width)
        else:
            self.sidebar_animation.setEndValue(expanded_width)

        self.sidebar_expanded = not self.sidebar_expanded
        self.sidebar_animation.start()


    def show_section(self, section: str) -> None:
        self.pages.setCurrentIndex(self.section_indexes[section])

    def apply_preferences(self, preferences: dict) -> None:
        self.preferences = preferences.copy()
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(application_stylesheet(preferences["theme"]))
        self.settings_view.apply_preferences(preferences)
        self.patients_view.apply_preferences(preferences)

    def _build_placeholder_page(self, title: str, message: str) -> QWidget:
        page = QWidget()
        page.setObjectName("PlaceholderPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 18)
        layout.setSpacing(8)
        layout.addWidget(QLabel(title, objectName="PageTitle"))

        body = QLabel(message, objectName="Muted")
        body.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(body)

        layout.addStretch()
        return page
