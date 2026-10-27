import sqlite3
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from app import config
from app.database.migrations.runner import MigrationBackupError, run_migrations
from app.services.backups import (
    BackupError,
    backup_directory,
    get_backup_manager,
    inspect_backup,
)
from app.services.preferences import load_preferences, save_preferences
from app.ui.main_window import MainWindow
from app.ui.theme import application_stylesheet


def prepare_database() -> bool:
    """Recovery remains available even when startup migrations cannot open the file."""
    marker = Path(str(config.DATABASE_PATH) + ".initialized")
    while True:
        try:
            if (
                not config.DATABASE_PATH.exists()
                or not config.DATABASE_PATH.stat().st_size
            ) and (marker.exists() or any(backup_directory().glob("edc-*.sqlite3"))):
                raise BackupError(
                    "The patient database is missing from an existing workspace."
                )
            run_migrations()
            inspect_backup(config.DATABASE_PATH)
            marker.write_text("EDC database initialized\n", encoding="utf-8")
            return True
        except MigrationBackupError as exc:
            QMessageBox.warning(
                None,
                "Database upgrade paused",
                f"{exc}\n\nChoose a working backup folder to continue.",
            )
            folder = QFileDialog.getExistingDirectory(
                None, "Choose backup folder before upgrading", str(backup_directory())
            )
            if not folder:
                return False
            try:
                save_preferences({**load_preferences(), "backup_directory": folder})
            except OSError as settings_error:
                QMessageBox.warning(
                    None, "Unable to save backup folder", str(settings_error)
                )
                return False
        except (sqlite3.Error, OSError, ValueError, BackupError) as exc:
            choice = QMessageBox.question(
                None,
                "Database recovery",
                f"The database could not be opened safely:\n{exc}\n\nRestore a database backup?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return False
            selected, _ = QFileDialog.getOpenFileName(
                None,
                "Select a database backup",
                str(backup_directory()),
                "Database backups (*.sqlite3 *.sqlite *.db);;All files (*)",
            )
            if not selected:
                return False
            try:
                info = inspect_backup(Path(selected))
                choice = QMessageBox.question(
                    None,
                    "Restore this backup?",
                    f"File date: {info.created_at:%Y-%m-%d %H:%M UTC}\n"
                    f"Patients: {info.patient_count}\n\n"
                    "All current patient data will be replaced. The current database "
                    "will be preserved as a recovery copy first.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if choice != QMessageBox.StandardButton.Yes:
                    return False
                result = get_backup_manager().restore(info.path)
                QMessageBox.information(
                    None,
                    "Database restored",
                    f"Restored {result.restored.patient_count} patient records.\nPrevious database: {result.recovery_path}",
                )
            except (BackupError, ValueError) as recovery_error:
                QMessageBox.warning(
                    None, "Unable to restore backup", str(recovery_error)
                )


def main() -> int:
    application = QApplication(sys.argv)
    preferences = load_preferences()
    application.setStyleSheet(application_stylesheet(preferences["theme"]))
    try:
        config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        QMessageBox.critical(None, "Unable to open database folder", str(exc))
        return 1
    lock = QLockFile(str(config.DATABASE_PATH) + ".lock")
    if not lock.tryLock(0):
        QMessageBox.warning(
            None,
            "Database already in use",
            "Another copy of the application is using this database. Close it before opening this copy.",
        )
        return 1
    try:
        if not prepare_database():
            return 1
        preferences = load_preferences()
        manager = get_backup_manager()
        manager.start()
        try:
            window = MainWindow(preferences)
            window.show()
            return application.exec()
        finally:
            manager.close()
    finally:
        lock.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
