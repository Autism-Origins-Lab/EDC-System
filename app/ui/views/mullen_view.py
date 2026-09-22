from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MullenView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()

        self.patient_id = patient_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Score Summary")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)

        self.score_table = QTableWidget()

        scales = [
            "Gross\nMotor",
            "Visual\nReception",
            "Fine\nMotor",
            "Receptive\nLanguage",
            "Expressive\nLanguage",
        ]

        headers = [
            "Scale",
            "Raw\nScore",
            "T Score\nM = 50, SD = 10",
            "Band of Error\n% Confidence",
            "Percentile\nRank",
            "Descriptive\nCategory",
            "Age\nEquivalent",
        ]

        self.score_table.setRowCount(len(scales))
        self.score_table.setColumnCount(len(headers))

        self.score_table.setHorizontalHeaderLabels(headers)

        for row, scale in enumerate(scales):
            item = QTableWidgetItem(scale)

            item.setFlags(
                item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.score_table.setItem(row, 0, item)

        self.raw_score_inputs = {}
        self.t_score_inputs = {}
        self.error_inputs = {}
        self.percentile_inputs = {}
        self.category_inputs = {}
        self.age_equivalent_inputs = {}

        for row in range(len(scales)):

            # Raw Score
            raw_input = self.create_input()
            self.score_table.setCellWidget(row, 1, raw_input)
            self.raw_score_inputs[row] = raw_input

            # T Score
            t_score_input = self.create_input()
            self.score_table.setCellWidget(row, 2, t_score_input)
            self.t_score_inputs[row] = t_score_input

            # Band of Error
            error_input = self.create_input(
                placeholder="+ / -"
            )
            self.score_table.setCellWidget(row, 3, error_input)
            self.error_inputs[row] = error_input

            # Percentile Rank
            percentile_input = self.create_input()
            self.score_table.setCellWidget(row, 4, percentile_input)
            self.percentile_inputs[row] = percentile_input

            # Descriptive Category
            category_input = self.create_input()
            self.score_table.setCellWidget(row, 5, category_input)
            self.category_inputs[row] = category_input

            # Age Equivalent
            age_input = self.create_input(placeholder="e.g. 24 months")
            self.score_table.setCellWidget(row, 6, age_input)
            self.age_equivalent_inputs[row] = age_input


        self.score_table.verticalHeader().setVisible(False)
        self.score_table.setShowGrid(True)
        self.score_table.setAlternatingRowColors(False)

        self.score_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        self.score_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        horizontal_header = self.score_table.horizontalHeader()

        horizontal_header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(4,QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(5,QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(6,QHeaderView.ResizeMode.Stretch)
        
        horizontal_header.setMinimumHeight(80)

       
        for row in range(len(scales)):
            self.score_table.setRowHeight(row, 75)


        layout.addWidget(self.score_table)

        self.save_button = QPushButton(
            "Save Mullen Scores"
        )

        self.save_button.setMinimumHeight(42)

        self.save_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
            }
        """)

        layout.addWidget(
            self.save_button,
            alignment=Qt.AlignmentFlag.AlignRight
        )

    def create_input(
        self,
        placeholder: str = ""
    ) -> QLineEdit:

        input_field = QLineEdit()

        input_field.setPlaceholderText(
            placeholder
        )

        input_field.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        return input_field