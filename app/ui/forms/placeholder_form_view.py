from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderFormView(QWidget):
    def __init__(self, title: str):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        heading = QLabel(title)
        heading.setObjectName("PageTitle")

        message = QLabel("This form will be migrated from the legacy app next.")
        message.setObjectName("Muted")
        message.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addStretch()
