import sys

from PySide6.QtWidgets import QApplication

from app.database.migration import run_migrations
from app.ui.main_window import MainWindow
from app.ui.theme import APP_STYLESHEET


def main() -> int:
    run_migrations()

    application = QApplication(sys.argv)
    application.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
