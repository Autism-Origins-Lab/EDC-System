import sys

from PySide6.QtWidgets import QApplication

from app.database.migrations.runner import run_migrations
from app.services.preferences import load_preferences
from app.ui.main_window import MainWindow
from app.ui.theme import application_stylesheet


def main() -> int:
    run_migrations()

    application = QApplication(sys.argv)
    preferences = load_preferences()
    application.setStyleSheet(application_stylesheet(preferences["theme"]))

    window = MainWindow(preferences)
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
