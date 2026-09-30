from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import get_mullen_assessment, save_mullen_assessment


class MullenView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()

        self.patient_id = patient_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Mullen Score Summary")
        title.setObjectName("PageTitle")
        title.setStyleSheet("color: #ffffff;")

        layout.addWidget(title)

        subtitle = QLabel(
            "Enter the score values for each developmental scale. "
            "Only the descriptive category accepts text."
        )
        subtitle.setObjectName("Muted")
        subtitle.setStyleSheet("color: #ffffff;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.score_table = QTableWidget()
        self.score_table.setObjectName("MullenScoreTable")

        self.scales = [
            ("gross_motor", "Gross\nMotor"),
            ("visual_reception", "Visual\nReception"),
            ("fine_motor", "Fine\nMotor"),
            ("receptive_language", "Receptive\nLanguage"),
            ("expressive_language", "Expressive\nLanguage"),
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

        self.score_table.setRowCount(len(self.scales))
        self.score_table.setColumnCount(len(headers))

        self.score_table.setHorizontalHeaderLabels(headers)

        for row, (_domain, scale_label) in enumerate(self.scales):
            item = QTableWidgetItem(scale_label)

            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            item.setBackground(QColor("#f8fafc"))
            item.setForeground(QColor("#1f2937"))

            scale_font = QFont(item.font())
            scale_font.setWeight(QFont.Weight.DemiBold)
            item.setFont(scale_font)

            self.score_table.setItem(row, 0, item)

        self.raw_score_inputs = {}
        self.t_score_inputs = {}
        self.error_inputs = {}
        self.percentile_inputs = {}
        self.category_inputs = {}
        self.age_equivalent_inputs = {}

        for row in range(len(self.scales)):
            # Raw Score
            raw_input = self.create_input(numeric=True)
            self.score_table.setCellWidget(row, 1, raw_input)
            self.raw_score_inputs[row] = raw_input

            # T Score
            t_score_input = self.create_input(numeric=True)
            self.score_table.setCellWidget(row, 2, t_score_input)
            self.t_score_inputs[row] = t_score_input

            # Band of Error
            error_input = self.create_input(
                placeholder="+ / -",
                numeric=True,
                allow_decimal=True,
            )
            self.score_table.setCellWidget(row, 3, error_input)
            self.error_inputs[row] = error_input

            # Percentile Rank
            percentile_input = self.create_input(numeric=True)
            self.score_table.setCellWidget(row, 4, percentile_input)
            self.percentile_inputs[row] = percentile_input

            # Descriptive Category
            category_input = self.create_input()
            self.score_table.setCellWidget(row, 5, category_input)
            self.category_inputs[row] = category_input

            # Age Equivalent
            age_input = self.create_input(placeholder="e.g. 24", numeric=True)
            self.score_table.setCellWidget(row, 6, age_input)
            self.age_equivalent_inputs[row] = age_input

        self.score_table.verticalHeader().setVisible(False)
        self.score_table.setCornerButtonEnabled(False)
        self.score_table.setWordWrap(True)
        self.score_table.setShowGrid(True)
        self.score_table.setAlternatingRowColors(True)

        self.score_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        self.score_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.score_table.setStyleSheet("""
            QTableWidget#MullenScoreTable {
                background-color: #ffffff;
                alternate-background-color: #fbfdff;
                border: 1px solid #dbe3ef;
                border-radius: 10px;
                gridline-color: #e8edf4;
                color: #1f2937;
            }

            QLabel#PageTitle{
                color: #ffffff
            }
            QTableWidget#MullenScoreTable::item {
                padding: 0 14px;
            }

            QTableWidget#MullenScoreTable QHeaderView::section {
                background-color: #eef4ff;
                color: #26415f;
                border: 0;
                border-right: 1px solid #dbe3ef;
                border-bottom: 1px solid #cdd9e8;
                font-size: 12px;
                font-weight: 600;
                padding: 10px 8px;
            }

            QTableWidget#MullenScoreTable QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                padding: 7px 9px;
                margin: 9px 7px;
            }

            QTableWidget#MullenScoreTable QLineEdit:hover {
                border-color: #94a3b8;
            }

            QTableWidget#MullenScoreTable QLineEdit:focus {
                background-color: #ffffff;
                border: 2px solid #1d63ed;
                padding: 6px 8px;
            }

            QTableWidget#MullenScoreTable QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)

        horizontal_header = self.score_table.horizontalHeader()

        horizontal_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        horizontal_header.setMinimumSectionSize(92)
        horizontal_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        horizontal_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setMinimumHeight(76)

        for row in range(len(self.scales)):
            self.score_table.setRowHeight(row, 68)

        layout.addWidget(self.score_table, 1)

        self.save_button = QPushButton("Save Mullen Scores")
        self.save_button.clicked.connect(self.save)

        self.save_button.setMinimumHeight(42)
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.load_existing_data()

    @staticmethod
    def integer_value(input_field: QLineEdit) -> int | None:
        value = input_field.text().strip()
        return int(value) if value else None

    @staticmethod
    def decimal_value(input_field: QLineEdit) -> float | None:
        value = input_field.text().strip()
        return float(value) if value else None

    def collect_data(self) -> dict:
        data = {}

        for row, (domain, _scale_label) in enumerate(self.scales):
            data[domain] = {
                "raw_score": self.integer_value(self.raw_score_inputs[row]),
                "t_score": self.integer_value(self.t_score_inputs[row]),
                "band_of_error": self.decimal_value(self.error_inputs[row]),
                "percentile_rank": self.integer_value(self.percentile_inputs[row]),
                "descriptive_category": (
                    self.category_inputs[row].text().strip() or None
                ),
                "age_equivalence": self.integer_value(self.age_equivalent_inputs[row]),
            }

        return data

    def load_existing_data(self) -> None:
        data = get_mullen_assessment(self.patient_id)

        input_fields = {
            "raw_score": self.raw_score_inputs,
            "t_score": self.t_score_inputs,
            "band_of_error": self.error_inputs,
            "percentile_rank": self.percentile_inputs,
            "descriptive_category": self.category_inputs,
            "age_equivalence": self.age_equivalent_inputs,
        }

        for row, (domain, _scale_label) in enumerate(self.scales):
            scores = data.get(domain)
            if not scores:
                continue

            for field, row_inputs in input_fields.items():
                value = scores.get(field)
                row_inputs[row].setText("" if value is None else str(value))

    def save(self) -> None:
        try:
            data = self.collect_data()
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Mullen Score",
                "Please enter numbers in every score field except "
                "Descriptive Category.",
            )
            return

        save_mullen_assessment(self.patient_id, data)
        QMessageBox.information(
            self,
            "Saved",
            "Mullen scores saved successfully.",
        )

    def create_input(
        self,
        placeholder: str = "",
        numeric: bool = False,
        allow_decimal: bool = False,
    ) -> QLineEdit:

        input_field = QLineEdit()

        input_field.setPlaceholderText(placeholder)

        input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if numeric:
            pattern = r"\d+(?:\.\d+)?" if allow_decimal else r"\d+"
            input_field.setValidator(
                QRegularExpressionValidator(
                    QRegularExpression(pattern),
                    input_field,
                )
            )

        return input_field
