"""Structured contact inputs that still read and write plain text.

Every class here exposes the same ``text()`` / ``setText()`` pair as QLineEdit, so
forms can load and collect them in one generic loop, and the values keep fitting
the existing TEXT columns without a database migration.
"""

import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

US_STATES = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"),
    ("DE", "Delaware"), ("DC", "District of Columbia"), ("FL", "Florida"),
    ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"), ("IL", "Illinois"),
    ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"), ("KY", "Kentucky"),
    ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"),
    ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"),
    ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"),
    ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
    ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"),
    ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"), ("SC", "South Carolina"), ("SD", "South Dakota"),
    ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
    ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"),
]


def digits_only(max_digits: int) -> QRegularExpressionValidator:
    """Blocks non-digits and anything past ``max_digits`` while typing."""
    return QRegularExpressionValidator(QRegularExpression(rf"\d{{0,{max_digits}}}"))


class ChoiceInput(QComboBox):
    """A dropdown with a blank "unanswered" first entry that stores a value
    which can differ from the label shown."""

    def __init__(self, options: list[tuple[str, str]]):
        super().__init__()
        self.addItem("", "")
        for value, label in options:
            self.addItem(label, value)

    def text(self) -> str:
        return self.currentData()

    def setText(self, value: str) -> None:
        # Older records were typed by hand, so match the stored value or the
        # label case-insensitively; anything else is kept as its own entry
        # rather than silently discarded.
        index = self.findData(value)
        if index < 0:
            labels = [self.itemText(i).casefold() for i in range(self.count())]
            index = labels.index(value.casefold()) if value.casefold() in labels else -1
        if index < 0:
            self.addItem(value, value)
            index = self.count() - 1
        self.setCurrentIndex(index)


class PhoneInput(QWidget):
    """Country code plus a 10-digit number, stored as ``"+1 5551234567"``."""

    NUMBER_DIGITS = 10
    STORED = re.compile(r"\+(\d{1,3}) (\d{10})")

    def __init__(self):
        super().__init__()
        self.country_code = QLineEdit()
        self.country_code.setPlaceholderText("1")
        self.country_code.setValidator(digits_only(3))
        self.country_code.setFixedWidth(60)
        self.number = QLineEdit()
        self.number.setPlaceholderText("10-digit number")
        self.number.setValidator(digits_only(self.NUMBER_DIGITS))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("+"))
        layout.addWidget(self.country_code)
        layout.addWidget(self.number, 1)

    def text(self) -> str:
        number = self.number.text().strip()
        # An empty number means unanswered, even if a country code was typed.
        if not number:
            return ""
        return f"+{self.country_code.text().strip() or '1'} {number}"

    def setText(self, value: str) -> None:
        match = self.STORED.fullmatch(value.strip())
        if match:
            code, number = match.groups()
        else:
            # Free-text legacy numbers such as "(555) 123-4567" are recovered
            # from their digits; a leading 1 on 11 digits is the US country code.
            digits = re.sub(r"\D", "", value)
            if len(digits) == 11 and digits.startswith("1"):
                code, number = "1", digits[1:]
            elif len(digits) == 10:
                code, number = "", digits
            else:
                # Unrecognizable: show it untouched so the save check flags it
                # for correction instead of the data being lost.
                code, number = "", value
        self.country_code.setText(code)
        self.number.setText(number)

    def is_valid(self) -> bool:
        number = self.number.text().strip()
        return not number or (number.isdigit() and len(number) == self.NUMBER_DIGITS)


class TimeOfDayInput(QWidget):
    """A 12-hour clock time plus AM/PM, stored as ``"10:30 AM"``."""

    TIME = r"(1[0-2]|0?[1-9])(:[0-5]\d)?"
    STORED = re.compile(rf"({TIME})\s*([AP]M)", re.IGNORECASE)

    def __init__(self):
        super().__init__()
        self.time = QLineEdit()
        self.time.setPlaceholderText("h:mm")
        self.time.setValidator(QRegularExpressionValidator(QRegularExpression(self.TIME)))
        self.meridiem = QComboBox()
        self.meridiem.addItems(["", "AM", "PM"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.time, 1)
        layout.addWidget(self.meridiem)

    def text(self) -> str:
        time = self.time.text().strip()
        return f"{time} {self.meridiem.currentText()}".strip() if time else ""

    def setText(self, value: str) -> None:
        match = self.STORED.fullmatch(value.strip())
        if match:
            self.time.setText(match.group(1))
            self.meridiem.setCurrentText(match.group(4).upper())
        else:
            # Legacy free text (e.g. "evenings") is shown as-is for correction.
            self.time.setText(value)
            self.meridiem.setCurrentIndex(0)

    def is_valid(self) -> bool:
        time = self.time.text().strip()
        return not time or (
            re.fullmatch(self.TIME, time) is not None and bool(self.meridiem.currentText())
        )
