from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
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

    def __init__(self, preferences: dict | None = None):
        super().__init__()
        self.preferences = preferences or load_preferences()
        self.setObjectName("SettingsView")

        layout = QVBoxLayout(self)
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
        layout.addStretch()

        self.apply_preferences(self.preferences)
        for combo in self.findChildren(SettingsComboBox):
            combo.currentTextChanged.connect(self._mark_changed)
        for checkbox in self.findChildren(QCheckBox, "SettingsOptionCheckBox"):
            checkbox.toggled.connect(self._mark_changed)

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
        self.unsaved_changes_checkbox.setChecked(
            preferences["warn_unsaved_changes"]
        )

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
        self.apply_preferences(DEFAULT_PREFERENCES)
        self.save_preferences()
