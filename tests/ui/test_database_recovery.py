from pathlib import Path

import pytest
from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app import config
from app import main as application
from app.database.repositories.patients import (
    create_patient,
    get_patient,
    update_patient,
)
from app.services import backups
from app.services.backups import BackupManager
from app.services.preferences import DEFAULT_PREFERENCES, load_preferences
from app.ui.dialogs.patient_detail_view import PatientDetailView
from app.ui.main_window import MainWindow
from app.ui.pages.settings_view import SettingsView
from app.ui.theme import application_stylesheet


@pytest.fixture
def recovery(temp_database, monkeypatch):
    manager = BackupManager(temp_database)
    monkeypatch.setattr(backups, "_manager", manager)
    messages = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args: messages.append(("info", args[-1]))
    )
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: messages.append(("warning", args[-1]))
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    yield manager, messages
    manager.close()


def test_settings_create_backup_and_restore_refreshes_patient_list(
    recovery, qtbot, monkeypatch
):
    manager, messages = recovery
    patient_id = create_patient("SETTINGS-BACKUP")
    window = MainWindow(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(window)
    settings = window.settings_view
    settings.create_backup_button.click()
    source = manager.last_backup
    assert source.exists()
    assert messages[-1][0] == "info"
    update_patient(patient_id, {"child_name": "Later name"})
    create_patient("LATER")
    window.patients_view.load_patients()
    assert len(window.patients_view.patients) == 2
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    settings.restore_backup_button.click()
    assert len(window.patients_view.patients) == 1
    assert get_patient(patient_id)["child_name"] is None
    assert "Previous database preserved" in messages[-1][1]


def test_restore_cancel_and_invalid_file_never_change_database(
    recovery, qtbot, monkeypatch, tmp_path
):
    manager, messages = recovery
    patient_id = create_patient("KEEP-CURRENT")
    source = manager.create_backup().path
    update_patient(patient_id, {"child_name": "Keep"})
    view = SettingsView(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(view)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No
    )
    view.restore_database_backup()
    assert get_patient(patient_id)["child_name"] == "Keep"
    assert not list(source.parent.glob("edc-before-restore-*.sqlite3"))
    invalid = tmp_path / "invalid.db"
    invalid.write_bytes(b"invalid")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *args: (str(invalid), "")
    )
    view.restore_database_backup()
    assert messages[-1][0] == "warning"
    assert get_patient(patient_id)["child_name"] == "Keep"


def test_restore_is_blocked_while_patient_drafts_are_open(recovery, qtbot, monkeypatch):
    _manager, messages = recovery
    patient_id = create_patient("DRAFT")
    dialog = PatientDetailView(patient_id, preferences=DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(dialog)
    dialog.overview_view.child_name_input.setText("Unsaved draft")
    dialog.show()
    settings = SettingsView(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(settings)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args: pytest.fail("Restore must not start with an open form"),
    )
    settings.restore_database_backup()
    assert "Close all patient forms" in messages[-1][1]
    assert dialog.overview_view.child_name_input.text() == "Unsaved draft"
    # Prevent pytest-qt teardown from opening an unsaved-changes prompt.
    dialog.preferences["warn_unsaved_changes"] = False


def test_choose_backup_folder_preserves_unsaved_preferences_and_restore_defaults(
    recovery, qtbot, monkeypatch, tmp_path
):
    folder = tmp_path / "separate-backups"
    view = SettingsView(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(view)
    view.theme_combo.setCurrentText("Dark")
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(folder))
    view.choose_backup_folder()
    assert view.theme_combo.currentText() == "Dark"
    assert load_preferences()["theme"] == "Light"
    assert backups.backup_directory() == folder
    view.restore_defaults()
    assert load_preferences()["backup_directory"] == str(folder)
    view.create_database_backup()
    assert list(folder.glob("edc-manual-*.sqlite3"))


def test_backup_error_is_visible_without_reporting_save_failure(recovery, qtbot):
    manager, _messages = recovery
    window = MainWindow(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(window)
    manager.last_error = "backup destination is offline"
    window.update_backup_status()
    window.settings_view.refresh_backup_status()
    assert (
        "Changes saved. Automatic backup failed" in window.statusBar().currentMessage()
    )
    assert "destination is offline" in window.settings_view.backup_status_label.text()
    manager.create_backup()
    window.update_backup_status()
    assert window.statusBar().currentMessage() == ""


def test_startup_recovers_corrupt_database_before_opening_main_window(
    recovery, monkeypatch
):
    manager, messages = recovery
    create_patient("STARTUP-RECOVERY")
    source = manager.create_backup().path
    manager.database.write_bytes(b"corrupted")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    assert application.prepare_database()
    assert get_patient(1)["subject_id"] == "STARTUP-RECOVERY"
    assert any(kind == "info" for kind, message in messages)
    assert list(source.parent.glob("edc-damaged-*.zip"))


def test_missing_database_offers_recovery_instead_of_silently_creating_empty(
    recovery, monkeypatch
):
    manager, _messages = recovery
    create_patient("MISSING-RECOVERY")
    source = manager.create_backup().path
    manager.database.unlink()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No
    )
    assert not application.prepare_database()
    assert not manager.database.exists()
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    assert application.prepare_database()
    assert get_patient(1)["subject_id"] == "MISSING-RECOVERY"


def test_database_instance_lock_prevents_second_process_lock(temp_database):
    first = QLockFile(str(config.DATABASE_PATH) + ".lock")
    second = QLockFile(str(config.DATABASE_PATH) + ".lock")
    try:
        assert first.tryLock(0)
        assert not second.tryLock(0)
    finally:
        first.unlock()
    assert second.tryLock(0)
    second.unlock()


def test_backup_settings_remain_accessible_in_small_window(recovery, qtbot, qapp):
    view = SettingsView(DEFAULT_PREFERENCES.copy())
    qtbot.addWidget(view)
    view.resize(720, 520)
    view.show()
    view.scroll_area.ensureWidgetVisible(view.restore_backup_button)
    qtbot.waitUntil(
        lambda: view.restore_backup_button.visibleRegion().isEmpty() is False
    )
    assert view.minimumSizeHint().width() <= 720
    # Render both themes for visual verification without reading patient data.
    output = Path(config.PROJECT_ROOT) / ".tmp" / "backup-ui"
    output.mkdir(parents=True, exist_ok=True)
    previous_style = qapp.styleSheet()
    try:
        qapp.setStyleSheet(application_stylesheet("Light"))
        qapp.processEvents()
        view.scroll_area.verticalScrollBar().setValue(
            view.scroll_area.verticalScrollBar().maximum()
        )
        view.grab().save(str(output / "settings-light.png"))
        qapp.setStyleSheet(application_stylesheet("Dark"))
        view.apply_preferences({**DEFAULT_PREFERENCES, "theme": "Dark"})
        qapp.processEvents()
        view.scroll_area.verticalScrollBar().setValue(
            view.scroll_area.verticalScrollBar().maximum()
        )
        view.grab().save(str(output / "settings-dark.png"))
    finally:
        qapp.setStyleSheet(previous_style)


def test_upgrade_backup_failure_offers_new_folder_without_restoring_data(
    recovery, monkeypatch, tmp_path
):
    _manager, messages = recovery
    create_patient("KEEP-DURING-UPGRADE")
    calls = []

    def migrate():
        calls.append(True)
        if len(calls) == 1:
            raise application.MigrationBackupError("backup destination unavailable")

    folder = tmp_path / "working-backups"
    monkeypatch.setattr(application, "run_migrations", migrate)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: str(folder))
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args: pytest.fail(
            "Changing the backup folder must not restore patient data"
        ),
    )
    assert application.prepare_database()
    assert len(calls) == 2
    assert load_preferences()["backup_directory"] == str(folder)
    assert get_patient(1)["subject_id"] == "KEEP-DURING-UPGRADE"
    assert any("Choose a working backup folder" in text for kind, text in messages)
