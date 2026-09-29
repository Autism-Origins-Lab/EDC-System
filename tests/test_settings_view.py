from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QCheckBox, QLabel

from app.ui.views.settings_view import SettingsComboBox, SettingsView


def test_settings_controls_have_view_specific_contrast(qtbot):
    view = SettingsView()
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
    view = SettingsView()
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
