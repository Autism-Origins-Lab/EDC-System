from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

YES = 1
NO = 0


class YesNoQuestion(QWidget):
    """A question with a Yes and a No radio button.

    value() returns 1 (Yes), 0 (No), or None (not answered yet).
    Keeping None separate from 0 means "not answered" is never saved as "No".
    """

    # Sent with 1, 0, or None whenever the answer is clicked or loaded
    answered = Signal(object)

    def __init__(
        self,
        text: str,
        help_text: str | None = None,
        yes_text: str = "Yes",
        no_text: str = "No",
    ):
        super().__init__()
        self.text = text

        # palette(window-text) is the system's text color: white in dark mode,
        # black in light mode, so the question matches the other form tabs.
        self.setStyleSheet(
            """
            QLabel#QuestionText, QRadioButton { color: palette(window-text); }
            QLabel#QuestionHelp { color: #9ca3af; font-size: 12px; font-style: italic; }
            QLabel#QuestionText:disabled, QLabel#QuestionHelp:disabled,
            QRadioButton:disabled { color: #6b7280; }
            """
        )

        self.question_label = QLabel(text)
        self.question_label.setObjectName("QuestionText")
        self.question_label.setWordWrap(True)

        self.yes_button = QRadioButton(yes_text)
        self.no_button = QRadioButton(no_text)
        self.yes_button.setAccessibleName(f"{text}: {yes_text}")
        self.no_button.setAccessibleName(f"{text}: {no_text}")

        # The group makes the two buttons exclusive and gives each an id,
        # so checkedId() tells us the answer directly.
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.yes_button, YES)
        self.button_group.addButton(self.no_button, NO)
        self.button_group.idClicked.connect(self.answered.emit)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.yes_button)
        buttons_row.addWidget(self.no_button)
        buttons_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.question_label)
        layout.addLayout(buttons_row)

        # Optional note for the RA only (not read aloud)
        self.help_label: QLabel | None = None
        if help_text:
            self.help_label = QLabel(help_text)
            self.help_label.setObjectName("QuestionHelp")
            self.help_label.setWordWrap(True)
            layout.addWidget(self.help_label)

    def value(self) -> int | None:
        checked_id = self.button_group.checkedId()
        if checked_id == -1:  # -1 means no button is checked
            return None
        return checked_id

    def set_value(self, value: int | None) -> None:
        if value is None:
            # An exclusive group won't let you uncheck its last checked
            # button, so turn exclusivity off just long enough to clear both.
            self.button_group.setExclusive(False)
            self.yes_button.setChecked(False)
            self.no_button.setChecked(False)
            self.button_group.setExclusive(True)
        elif value == YES:
            self.yes_button.setChecked(True)
        elif value == NO:
            self.no_button.setChecked(True)
        else:
            raise ValueError(f"Expected 1, 0, or None for {self.text!r}, got {value!r}")

        # Tell listeners too, so follow-up questions appear when saved data loads
        self.answered.emit(self.value())
