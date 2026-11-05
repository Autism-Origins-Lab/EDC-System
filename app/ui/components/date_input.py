from PySide6.QtWidgets import QLineEdit

from app.services.preferences import DATE_FORMAT


class DateInput(QLineEdit):
    """A date box where the user types only the 8 digits of MM-DD-YYYY.

    An input mask is used instead of a validator because it does both jobs at
    once: non-digits are rejected as they are typed, and the dashes are filled
    in automatically, so "03012025" becomes "03-01-2025".
    """

    def __init__(self):
        super().__init__()
        self.setInputMask("99-99-9999;_")
        self.setToolTip(f"Type the date as {DATE_FORMAT}; the dashes are added for you.")

    def keyPressEvent(self, event):
        first_blank = self.displayText().find("_")
        if 0 <= first_blank < self.cursorPosition():
            self.setCursorPosition(first_blank)
        super().keyPressEvent(event)

    def text(self) -> str:
        text = super().text()
        return text if any(character.isdigit() for character in text) else ""
