from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout


class Sidebar(QFrame):
    section_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self.buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(6)

        items = [
            "Patients",
            "Telephone Screening",
            "Questionnaires",
            "Medical History",
            "Family History",
            "Imports",
            "Exports",
            "Settings",
        ]

        for label in items:
            button = QPushButton(label)
            button.setProperty("nav", True)
            button.setProperty("active", label == "Patients")
            button.clicked.connect(lambda _checked=False, section=label: self.select_section(section))
            self.buttons[label] = button
            layout.addWidget(button)

        layout.addStretch()

    def select_section(self, section: str) -> None:
        for label, button in self.buttons.items():
            button.setProperty("active", label == section)
            button.style().unpolish(button)
            button.style().polish(button)

        self.section_selected.emit(section)
