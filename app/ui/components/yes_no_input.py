from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QSizePolicy


class _QuestionLabel(QLabel):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        required = self.heightForWidth(self.width())
        if required > 0 and self.minimumHeight() != required:
            self.setMinimumHeight(required)


class YesNoInput(QComboBox):
    """An optional answer that keeps unanswered, Yes, and No distinct."""

    def __init__(self, question: str):
        super().__init__()
        self.question = question
        self.setAccessibleName(question)
        self.addItem("Not answered", None)
        self.addItem("Yes", 1)
        self.addItem("No", 0)

    def value(self) -> int | None:
        return self.currentData()

    def set_value(self, value: int | None) -> None:
        if value is not None and (
            type(value) not in (int, bool) or value not in (0, 1)
        ):
            raise ValueError(f"{self.question} must be Yes, No, or unanswered.")
        self.setCurrentIndex(self.findData(None if value is None else int(value)))

    def add_to_form(self, form: QFormLayout) -> None:
        label = _QuestionLabel(self.question)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        label.setBuddy(self)
        form.addRow(label, self)
