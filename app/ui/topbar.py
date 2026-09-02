from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit

from app.config import APP_NAME


class TopBar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(24)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")

        search = QLineEdit()
        search.setObjectName("GlobalSearch")
        search.setPlaceholderText("Search patients, forms, exports")
        search.setFixedWidth(420)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(search)
