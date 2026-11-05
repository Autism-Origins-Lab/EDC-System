from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QScrollArea, QVBoxLayout, QWidget

from app.ui.components.dropdown_wheel_guard import install_dropdown_wheel_guard


def _scroll_down(widget):
    event = QWheelEvent(
        QPointF(5, 5),
        QPointF(widget.mapToGlobal(QPoint(5, 5))),
        QPoint(),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(widget, event)


def test_wheel_over_closed_dropdown_scrolls_page_instead_of_changing_it(qtbot, qapp):
    guard = install_dropdown_wheel_guard(qapp)
    try:
        page = QWidget()
        layout = QVBoxLayout(page)
        combo = QComboBox()
        combo.addItems(["", "Female", "Male"])
        layout.addWidget(combo)
        page.setMinimumHeight(2000)  # tall enough that the page must scroll
        area = QScrollArea()
        area.setWidget(page)
        area.resize(300, 200)
        qtbot.addWidget(area)
        area.show()

        _scroll_down(combo)

        assert combo.currentText() == ""
        assert area.verticalScrollBar().value() > 0
    finally:
        qapp.removeEventFilter(guard)
