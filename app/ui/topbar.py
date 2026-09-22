from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

from app.config import APP_NAME


class TopBar(QFrame):
    menu_clicked = Signal()
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(58)

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
        search.setPlaceholderText("Search patients, forms, exports")
        search.setFixedWidth(420)

        layout.addWidget(menu_button)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(search)