from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 18)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")

        subtitle = QLabel("Adjust local display preferences for this EDC workspace.")
        subtitle.setObjectName("Muted")

        preferences_card = QFrame()
        preferences_card.setObjectName("SettingsCard")

        form = QFormLayout(preferences_card)
        form.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])

        self.row_density_combo = QComboBox()
        self.row_density_combo.addItems(["Comfortable", "Compact"])

        self.start_page_combo = QComboBox()
        self.start_page_combo.addItems(["Patients", "Exports", "Settings"])

        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "YYYY-MM-DD"])

        self.confirm_delete_checkbox = QCheckBox("Confirm before deleting patient records")
        self.confirm_delete_checkbox.setChecked(True)

        self.unsaved_changes_checkbox = QCheckBox("Warn before closing forms with unsaved changes")
        self.unsaved_changes_checkbox.setChecked(True)

        form.addRow("Theme", self.theme_combo)
        form.addRow("Table Row Density", self.row_density_combo)
        form.addRow("Startup Page", self.start_page_combo)
        form.addRow("Date Format", self.date_format_combo)
        form.addRow("", self.confirm_delete_checkbox)
        form.addRow("", self.unsaved_changes_checkbox)

        save_button = QPushButton("Save Preferences")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_preferences)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(preferences_card)
        layout.addWidget(save_button)
        layout.addStretch()

    def collect_preferences(self) -> dict:
        return {
            "theme": self.theme_combo.currentText(),
            "row_density": self.row_density_combo.currentText(),
            "startup_page": self.start_page_combo.currentText(),
            "date_format": self.date_format_combo.currentText(),
            "confirm_delete": self.confirm_delete_checkbox.isChecked(),
            "warn_unsaved_changes": self.unsaved_changes_checkbox.isChecked(),
        }

    def save_preferences(self) -> None:
        preferences = self.collect_preferences()
        print(preferences)