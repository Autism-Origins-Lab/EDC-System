from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QComboBox


class DropdownWheelGuard(QObject):
    #Stops the mouse wheel from changing a dropdown that is not open.

    def eventFilter(self, watched, event) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(watched, QComboBox)
            and not watched.view().isVisible()
        ):
            scroll_bar = self._nearest_scroll_bar(watched)
            if scroll_bar is not None:
                # Qt does not pass a re-sent wheel event up to parent widgets,
                # so it goes straight to the scroll bar of the page around the
                # dropdown (the same approach PatientsView uses for its table).
                QApplication.sendEvent(scroll_bar, event)
            return True  # the closed dropdown itself never sees the wheel
        return super().eventFilter(watched, event)

    @staticmethod
    def _nearest_scroll_bar(widget):
        ancestor = widget.parentWidget()
        while ancestor is not None:
            if isinstance(ancestor, QAbstractScrollArea):
                bar = ancestor.verticalScrollBar()
                if bar.maximum() > bar.minimum():
                    return bar
            ancestor = ancestor.parentWidget()
        return None


def install_dropdown_wheel_guard(application: QApplication) -> DropdownWheelGuard:
    # Parenting the guard to the application keeps it alive as long as the app.
    guard = DropdownWheelGuard(application)
    application.installEventFilter(guard)
    return guard
