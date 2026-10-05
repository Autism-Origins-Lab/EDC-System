from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Signal

from app.config import APP_NAME

class TopBar(QFrame):
    menu_clicked = Signal()

    #raw text user typed so that PatientsView can combine the text w filter in one place.
    search_changed = Signal(str)
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(58)
        self.setStyleSheet("QFrame#TopBar { background-color: #166AB8;}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(24)

        menu_button = QPushButton(chr(9776))
        menu_button.setObjectName("BurgerMenu")
        menu_button.setFixedSize(38,38)
        menu_button.clicked.connect(self.menu_clicked.emit)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")

        search = QLineEdit()
        search.setObjectName("GlobalSearch")
        search.setPlaceholderText("Search for a specific patient (Child name or Child name, Subject  ID)")
        search.setFixedWidth(420)
        search.setStyleSheet("border-radius: 9999px")
        search.textChanged.connect(self.search_changed.emit)

        layout.addWidget(menu_button)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(search)