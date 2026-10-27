from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.backups import (
    BackupError,
    backup_directory,
    get_backup_manager,
    inspect_backup,
)
from app.services.preferences import (
    DEFAULT_PREFERENCES,
    load_preferences,
    save_preferences,
)
from app.ui.theme import (
    DARK_SETTINGS_STYLESHEET,
    SETTINGS_ARROW_COLOR,
    SETTINGS_ARROW_STROKE_WIDTH,
    SETTINGS_DISABLED_ARROW_COLOR,
    SETTINGS_STYLESHEET,
    themed_stylesheet,
)


class SettingsComboBox(QComboBox):
    """Combo box with a dropdown chevron styled by the central theme."""

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        arrow_color = (
            SETTINGS_ARROW_COLOR if self.isEnabled() else SETTINGS_DISABLED_ARROW_COLOR
        )
        pen = QPen(QColor(arrow_color), SETTINGS_ARROW_STROKE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        center_x = self.width() - 16
        center_y = self.height() / 2
        painter.drawLine(
            QPointF(center_x - 3, center_y - 1.5),
            QPointF(center_x, center_y + 1.5),
        )
        painter.drawLine(
            QPointF(center_x, center_y + 1.5),
            QPointF(center_x + 3, center_y - 1.5),
        )


class SettingsView(QWidget):
    preferences_saved = Signal(dict)
    database_restored = Signal()

    def __init__(self, preferences: dict | None = None):
        super().__init__()
        self.preferences = preferences or load_preferences()
        self.setObjectName("SettingsView")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("SettingsContent")
        self.scroll_area.setWidget(content)
        root.addWidget(self.scroll_area)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 28, 28, 18)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Adjust local preferences for this EDC workspace.")
        subtitle.setObjectName("Muted")

        preferences_card = QFrame()
        preferences_card.setObjectName("SettingsCard")
        form = QFormLayout(preferences_card)
        form.setSpacing(12)

        self.theme_combo = SettingsComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.row_density_combo = SettingsComboBox()
        self.row_density_combo.addItems(["Comfortable", "Compact"])
        self.start_page_combo = SettingsComboBox()
        self.start_page_combo.addItems(["Patients", "Imports", "Exports", "Settings"])
        self.date_format_combo = SettingsComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "YYYY-MM-DD"])

        self.confirm_delete_checkbox = QCheckBox(
            "Confirm before deleting patient records"
        )
        self.confirm_delete_checkbox.setObjectName("SettingsOptionCheckBox")
        self.unsaved_changes_checkbox = QCheckBox(
            "Warn before closing forms with unsaved changes"
        )
        self.unsaved_changes_checkbox.setObjectName("SettingsOptionCheckBox")

        form.addRow(self._option_label("Theme"), self.theme_combo)
        form.addRow(self._option_label("Table Row Density"), self.row_density_combo)
        form.addRow(self._option_label("Startup Page"), self.start_page_combo)
        form.addRow(self._option_label("Date Format"), self.date_format_combo)
        form.addRow("", self.confirm_delete_checkbox)
        form.addRow("", self.unsaved_changes_checkbox)

        self.save_button = QPushButton("Save Preferences")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_preferences)
        reset_button = QPushButton("Restore Defaults")
        reset_button.setObjectName("SecondaryButton")
        reset_button.clicked.connect(self.restore_defaults)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(reset_button)
        actions.addStretch()

        self.status_label = QLabel()
        self.status_label.setObjectName("SettingsStatus")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(preferences_card)
        layout.addLayout(actions)
        layout.addWidget(self.status_label)
        backup_card = QFrame()
        backup_card.setObjectName("SettingsCard")
        backup_layout = QVBoxLayout(backup_card)
        backup_title = QLabel("Database backup and restore")
        backup_title.setObjectName("BackupTitle")
        backup_layout.addWidget(backup_title)
        description = QLabel(
            "Backups contain saved patient records and video references. "
            "Video files and application preferences are stored separately. "
            "Choose a folder on a separate device for protection against drive failure."
        )
        description.setWordWrap(True)
        backup_layout.addWidget(description)
        self.backup_location_label = QLabel()
        self.backup_location_label.setWordWrap(True)
        self.backup_location_label.setTextFormat(Qt.TextFormat.PlainText)
        backup_layout.addWidget(self.backup_location_label)
        self.backup_status_label = QLabel()
        self.backup_status_label.setWordWrap(True)
        self.backup_status_label.setTextFormat(Qt.TextFormat.PlainText)
        backup_layout.addWidget(self.backup_status_label)
        backup_actions = QHBoxLayout()
        self.backup_folder_button = QPushButton("Choose Backup Folder…")
        self.backup_folder_button.setObjectName("SecondaryButton")
        self.backup_folder_button.clicked.connect(self.choose_backup_folder)
        self.create_backup_button = QPushButton("Create Backup")
        self.create_backup_button.setObjectName("SecondaryButton")
        self.create_backup_button.clicked.connect(self.create_database_backup)
        self.restore_backup_button = QPushButton("Restore Backup…")
        self.restore_backup_button.setObjectName("SecondaryButton")
        self.restore_backup_button.clicked.connect(self.restore_database_backup)
        for button in (
            self.backup_folder_button,
            self.create_backup_button,
            self.restore_backup_button,
        ):
            backup_actions.addWidget(button)
        backup_actions.addStretch()
        backup_layout.addLayout(backup_actions)
        retention = QLabel(
            "Automatic backups keep the 20 most recent copies plus one per backup day "
            "for up to 30 backup days. Manual and recovery copies are kept."
        )
        retention.setWordWrap(True)
        backup_layout.addWidget(retention)
        layout.addWidget(backup_card)
        layout.addStretch()

        self.apply_preferences(self.preferences)
        for combo in self.findChildren(SettingsComboBox):
            combo.currentTextChanged.connect(self._mark_changed)
        for checkbox in self.findChildren(QCheckBox, "SettingsOptionCheckBox"):
            checkbox.toggled.connect(self._mark_changed)
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self.refresh_backup_status)
        self.backup_timer.start(1000)
        self.refresh_backup_status()

    @staticmethod
    def _option_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SettingsOptionLabel")
        return label

    def collect_preferences(self) -> dict:
        return {
            "theme": self.theme_combo.currentText(),
            "row_density": self.row_density_combo.currentText(),
            "startup_page": self.start_page_combo.currentText(),
            "date_format": self.date_format_combo.currentText(),
            "confirm_delete": self.confirm_delete_checkbox.isChecked(),
            "warn_unsaved_changes": self.unsaved_changes_checkbox.isChecked(),
            "backup_directory": self.preferences.get("backup_directory", ""),
        }

    def apply_preferences(self, preferences: dict) -> None:
        self.preferences = preferences.copy()
        self.setStyleSheet(
            themed_stylesheet(
                SETTINGS_STYLESHEET,
                DARK_SETTINGS_STYLESHEET,
                preferences["theme"],
            )
        )
        self.theme_combo.setCurrentText(preferences["theme"])
        self.row_density_combo.setCurrentText(preferences["row_density"])
        self.start_page_combo.setCurrentText(preferences["startup_page"])
        self.date_format_combo.setCurrentText(preferences["date_format"])
        self.confirm_delete_checkbox.setChecked(preferences["confirm_delete"])
        self.unsaved_changes_checkbox.setChecked(preferences["warn_unsaved_changes"])

    def _mark_changed(self, *_args) -> None:
        self.status_label.setText("Unsaved preference changes")

    def save_preferences(self) -> None:
        try:
            self.preferences = save_preferences(self.collect_preferences())
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Unable to save preferences",
                f"The preferences file could not be saved: {exc}",
            )
            return
        self.status_label.setText("Preferences saved")
        self.preferences_saved.emit(self.preferences.copy())

    def restore_defaults(self) -> None:
        self.apply_preferences(
            {
                **DEFAULT_PREFERENCES,
                "backup_directory": self.preferences.get("backup_directory", ""),
            }
        )
        self.save_preferences()

    def refresh_backup_status(self) -> None:
        directory = backup_directory()
        self.backup_location_label.setText(f"Backup folder: {directory}")
        manager = get_backup_manager()
        if manager.last_error:
            self.backup_status_label.setText(
                f"Changes saved. Automatic backup failed: {manager.last_error}"
            )
        else:
            latest = manager.last_backup
            if latest is not None and latest.parent.resolve() != directory.resolve():
                latest = None
            if latest is None:
                try:
                    latest = max(
                        directory.glob("edc-*.sqlite3"),
                        key=lambda file: file.stat().st_mtime,
                        default=None,
                    )
                except OSError:
                    latest = None
            self.backup_status_label.setText(
                f"Last backup: {latest.name}"
                if latest
                else "No database backup has been created yet."
            )

    def choose_backup_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose backup folder", str(backup_directory())
        )
        if not chosen:
            return
        try:
            # Save this setting without discarding other preference edits on screen.
            preferences = save_preferences(
                {**load_preferences(), "backup_directory": chosen}
            )
            self.preferences["backup_directory"] = preferences["backup_directory"]
            # The directory is used directly by the backup service. Avoid emitting
            # a full preference reload that would overwrite unsaved screen edits.
            manager = get_backup_manager()
            manager.last_error = None
            manager.after_commit()
        except OSError as exc:
            QMessageBox.warning(self, "Unable to change backup folder", str(exc))
            return
        self.refresh_backup_status()

    def create_database_backup(self) -> None:
        try:
            info = get_backup_manager().create_backup()
        except BackupError as exc:
            QMessageBox.warning(self, "Unable to create backup", str(exc))
            return
        self.refresh_backup_status()
        QMessageBox.information(
            self,
            "Backup created",
            f"Saved {info.patient_count} patient records to:\n{info.path}",
        )

    def restore_database_backup(self) -> None:
        from app.ui.dialogs.patient_detail_view import PatientDetailView

        if any(
            isinstance(widget, PatientDetailView) and widget.isVisible()
            for widget in QApplication.topLevelWidgets()
        ):
            QMessageBox.warning(
                self,
                "Close patient forms",
                "Close all patient forms before restoring. You can save or discard their drafts when closing them.",
            )
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a database backup",
            str(backup_directory()),
            "Database backups (*.sqlite3 *.sqlite *.db);;All files (*)",
        )
        if not path:
            return
        try:
            info = inspect_backup(Path(path))
            choice = QMessageBox.question(
                self,
                "Restore database backup?",
                f"File date: {info.created_at:%Y-%m-%d %H:%M UTC}\n"
                f"Patients: {info.patient_count}\n\n"
                "This replaces all current patient records with the selected backup. "
                "Later additions and edits will no longer appear. "
                "A recovery copy of the current database will be kept first.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            result = get_backup_manager().restore(info.path)
        except (BackupError, ValueError) as exc:
            QMessageBox.warning(self, "Unable to restore backup", str(exc))
            return
        self.database_restored.emit()
        self.refresh_backup_status()
        message = f"Restored {result.restored.patient_count} patient records."
        if result.recovery_path:
            message += f"\nPrevious database preserved at:\n{result.recovery_path}"
        QMessageBox.information(self, "Database restored", message)
