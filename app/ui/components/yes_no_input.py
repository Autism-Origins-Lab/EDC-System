from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class _QuestionLabel(QLabel):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        required = self.heightForWidth(self.width())
        if required > 0 and self.minimumHeight() != required:
            self.setMinimumHeight(required)


class YesNoInput(QWidget):
    """An optional answer that keeps unanswered, Yes, and No distinct."""

    OPTIONS = (("Yes", 1), ("No", 0), ("Not answered", None))

    valueChanged = Signal(object)

    def __init__(self, question: str):
        super().__init__()
        self.question = question
        self.setAccessibleName(question)
        self.input_group = QButtonGroup(self)
        self.input_group.setExclusive(True)
        self._buttons: dict[int | None, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for text, value in self.OPTIONS:
            button = QPushButton(text)
            button.setObjectName("AnswerBubble")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName(f"{question}: {text}")
            button.clicked.connect(lambda _checked, v=value: self.valueChanged.emit(v))
            self.input_group.addButton(button)
            self._buttons[value] = button
            layout.addWidget(button)
        layout.addStretch()
        self._buttons[None].setChecked(True)

    def value(self) -> int | None:
        for value, button in self._buttons.items():
            if button.isChecked():
                return value
        return None

    def currentText(self) -> str:
        return self.input_group.checkedButton().text()

    def set_value(self, value: int | None) -> None:
        if value is not None and (
            type(value) not in (int, bool) or value not in (0, 1)
        ):
            raise ValueError(f"{self.question} must be Yes, No, or unanswered.")
        value = None if value is None else int(value)
        if value != self.value():
            self._buttons[value].setChecked(True)
            self.valueChanged.emit(value)

    def add_to_form(self, form: QFormLayout) -> None:
        label = _QuestionLabel(self.question)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        label.setBuddy(self)
        form.addRow(label, self)
