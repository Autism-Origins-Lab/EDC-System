from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.videos import create_patient_video, list_patient_videos


class VideoReferencesView(QWidget):
    """Store local video paths without copying the underlying files."""

    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        group = QGroupBox("Add video reference")
        form = QFormLayout(group)
        form.setContentsMargins(24, 30, 24, 24)
        self.title_input = QLineEdit()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("Choose a local video file")
        browse = QPushButton("Browse…")
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.clicked.connect(self.choose_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_path_input, 1)
        file_row.addWidget(browse)
        form.addRow("Title", self.title_input)
        form.addRow("Video file", file_row)
        layout.addWidget(group)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Title", "File path"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table, 1)
        self.load_existing_data()

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose video",
            "",
            "Video files (*.mp4 *.mov *.avi *.mkv *.wmv *.m4v);;All files (*)",
        )
        if path:
            self.file_path_input.setText(path)

    def load_existing_data(self) -> None:
        videos = list_patient_videos(self.patient_id)
        self.table.setRowCount(len(videos))
        for row, video in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(video.get("title") or ""))
            self.table.setItem(row, 1, QTableWidgetItem(video.get("file_path") or ""))

    def save(self) -> bool:
        create_patient_video(
            self.patient_id,
            {
                "title": self.title_input.text().strip(),
                "file_path": self.file_path_input.text().strip(),
            },
        )
        self.title_input.clear()
        self.file_path_input.clear()
        self.load_existing_data()
        return True
