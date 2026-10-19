from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QCheckBox, QLabel

from app import config
from app.services.preferences import DEFAULT_PREFERENCES, load_preferences
from app.ui.main_window import MainWindow
from app.ui.pages.settings_view import SettingsComboBox, SettingsView


def test_settings_controls_have_view_specific_contrast(qtbot):
    view = SettingsView(DEFAULT_PREFERENCES)
    qtbot.addWidget(view)
    view.resize(720, 520)
    view.show()

    labels = view.findChildren(QLabel, "SettingsOptionLabel")
    checkboxes = view.findChildren(QCheckBox, "SettingsOptionCheckBox")
    combo_boxes = view.findChildren(SettingsComboBox)

    assert len(labels) == 4
    assert len(checkboxes) == 2
    assert len(combo_boxes) == 4
    assert all(
        label.palette().color(QPalette.ColorRole.WindowText).name() == "#1f2937"
        for label in labels
    )
    assert all(
        checkbox.palette().color(QPalette.ColorRole.WindowText).name() == "#1f2937"
        for checkbox in checkboxes
    )
    assert all(
        combo.palette().color(QPalette.ColorRole.Text).name() == "#111827"
        for combo in combo_boxes
    )


def test_settings_combo_uses_transparent_dropdown_and_gray_chevron(qtbot):
    view = SettingsView(DEFAULT_PREFERENCES)
    qtbot.addWidget(view)
    view.resize(720, 520)
    view.show()

    combo = view.theme_combo
    stylesheet = view.styleSheet()
    assert "QComboBox::drop-down" in stylesheet
    assert "background-color: transparent" in stylesheet
    assert "QComboBox::down-arrow" in stylesheet
    assert "image: none" in stylesheet

    image = combo.grab().toImage()
    expected_arrow = QColor("#9ca3af")
    center_y = combo.height() // 2
    arrow_pixels = (
        QColor(image.pixel(x, y))
        for x in range(combo.width() - 20, combo.width() - 11)
        for y in range(center_y - 5, center_y + 6)
    )

    assert any(
        abs(color.red() - expected_arrow.red()) <= 20
        and abs(color.green() - expected_arrow.green()) <= 20
        and abs(color.blue() - expected_arrow.blue()) <= 20
        for color in arrow_pixels
    )


def test_settings_save_preferences_and_emit_change(qtbot, monkeypatch, tmp_path):
    preferences_path = tmp_path / "preferences.json"
    monkeypatch.setattr(config, "PREFERENCES_PATH", preferences_path)
    view = SettingsView(DEFAULT_PREFERENCES)
    qtbot.addWidget(view)
    saved = []
    view.preferences_saved.connect(saved.append)

    view.theme_combo.setCurrentText("Dark")
    view.row_density_combo.setCurrentText("Compact")
    view.start_page_combo.setCurrentText("Exports")
    view.date_format_combo.setCurrentText("MM/DD/YYYY")
    view.confirm_delete_checkbox.setChecked(False)
    view.unsaved_changes_checkbox.setChecked(False)
    view.save_button.click()

    assert view.status_label.text() == "Preferences saved"
    assert saved == [load_preferences()]
    assert saved[0] == view.collect_preferences()


def test_main_window_applies_startup_page_and_row_density(temp_database, qtbot):
    preferences = {
        **DEFAULT_PREFERENCES,
        "startup_page": "Settings",
        "row_density": "Compact",
    }
    window = MainWindow(preferences)
    qtbot.addWidget(window)

    assert window.pages.currentIndex() == window.section_indexes["Settings"]
    assert window.sidebar.buttons["Settings"].property("active") is True
    assert window.patients_view.table.verticalHeader().defaultSectionSize() == 34
