from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
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


class SettingsComboBox(QComboBox):
    """Combo box with a simple, theme-independent dropdown chevron."""

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        arrow_color = "#9ca3af" if self.isEnabled() else "#d1d5db"
        pen = QPen(QColor(arrow_color), 1.5)
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
    def __init__(self):
        super().__init__()
        self.setObjectName("SettingsView")
        self.setStyleSheet(
            """
            QWidget#SettingsView QLabel#SettingsOptionLabel,
            QWidget#SettingsView QCheckBox#SettingsOptionCheckBox {
                color: #1f2937;
            }

            QWidget#SettingsView QComboBox {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px 32px 7px 10px;
            }

            QWidget#SettingsView QComboBox:hover,
            QWidget#SettingsView QComboBox:focus {
                border-color: #1d63ed;
            }

            QWidget#SettingsView QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                background-color: transparent;
                border: none;
            }

            QWidget#SettingsView QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }

            QWidget#SettingsView QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                selection-background-color: #eaf1ff;
                selection-color: #1d63ed;
                border: 1px solid #d1d5db;
            }
            """
        )

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

        self.theme_combo = SettingsComboBox()
        self.theme_combo.addItems(["Light", "Dark"])

        self.row_density_combo = SettingsComboBox()
        self.row_density_combo.addItems(["Comfortable", "Compact"])

        self.start_page_combo = SettingsComboBox()
        self.start_page_combo.addItems(["Patients", "Exports", "Settings"])

        self.date_format_combo = SettingsComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "YYYY-MM-DD"])

        self.confirm_delete_checkbox = QCheckBox("Confirm before deleting patient records")
        self.confirm_delete_checkbox.setObjectName("SettingsOptionCheckBox")
        self.confirm_delete_checkbox.setChecked(True)

        self.unsaved_changes_checkbox = QCheckBox("Warn before closing forms with unsaved changes")
        self.unsaved_changes_checkbox.setObjectName("SettingsOptionCheckBox")
        self.unsaved_changes_checkbox.setChecked(True)

        form.addRow(self._option_label("Theme"), self.theme_combo)
        form.addRow(self._option_label("Table Row Density"), self.row_density_combo)
        form.addRow(self._option_label("Startup Page"), self.start_page_combo)
        form.addRow(self._option_label("Date Format"), self.date_format_combo)
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

    def save_preferences(self) -> None:
        preferences = self.collect_preferences()
        print(preferences)
