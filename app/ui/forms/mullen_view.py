from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
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

from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
    save_mullen_assessment,
)
from app.database.repositories.patients import get_patient
from app.services.mullen_scoring import MullenScoringError, auto_score, calculate_age
from app.services.preferences import format_date, load_preferences, parse_date
from app.ui.theme import (
    DARK_MULLEN_STYLESHEET,
    MULLEN_SCALE_BACKGROUND_COLOR,
    MULLEN_SCALE_FONT_WEIGHT,
    MULLEN_SCALE_TEXT_COLOR,
    MULLEN_SCORE_TABLE_STYLESHEET,
    MULLEN_SUBTITLE_STYLESHEET,
    MULLEN_TITLE_STYLESHEET,
    themed_stylesheet,
)


class MullenView(QWidget):
    def __init__(self, patient_id: int, preferences: dict | None = None):
        super().__init__()

        self.patient_id = patient_id
        self._loading = False
        self.preferences = preferences or load_preferences()
        self.date_format = self.preferences["date_format"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Mullen Score Summary")
        title.setObjectName("PageTitle")
        title.setStyleSheet(MULLEN_TITLE_STYLESHEET)

        layout.addWidget(title)

        subtitle = QLabel(
            "Enter raw scores to fill T scores, error widths, percentiles, and categories. "
            "The supplied tables cover birth through 4 months, 30 days."
        )
        subtitle.setObjectName("Muted")
        subtitle.setStyleSheet(MULLEN_SUBTITLE_STYLESHEET)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        context_form = QFormLayout()
        self.date_of_birth_input = QLineEdit()
        self.date_of_birth_input.setReadOnly(True)
        self.date_of_birth_input.setPlaceholderText("Save date of birth in Overview")
        self.use_overview_dob_button = QPushButton("Use Overview DOB")
        self.use_overview_dob_button.clicked.connect(self.use_overview_dob)
        dob_row = QHBoxLayout()
        dob_row.addWidget(self.date_of_birth_input, 1)
        dob_row.addWidget(self.use_overview_dob_button)
        context_form.addRow("Date of birth used", dob_row)

        self.assessment_date_input = QLineEdit()
        self.assessment_date_input.setPlaceholderText(self.date_format)
        context_form.addRow("Assessment date", self.assessment_date_input)
        self.confidence_combo = QComboBox()
        self.confidence_combo.addItem("Select confidence", None)
        self.confidence_combo.addItem("90%", 90)
        self.confidence_combo.addItem("95%", 95)
        context_form.addRow("Confidence level", self.confidence_combo)
        self.age_calculation_combo = QComboBox()
        self.age_calculation_combo.addItem("Select handbook age convention", None)
        self.age_calculation_combo.addItem("Calendar months", "calendar")
        self.age_calculation_combo.addItem("30-day borrowing", "30_day_borrow")
        context_form.addRow("Age calculation", self.age_calculation_combo)
        layout.addLayout(context_form)
        self.age_label = QLabel()
        layout.addWidget(self.age_label)
        coverage_note = QLabel(
            "Automatic scoring is available from birth through 4 months, 30 days."
        )
        coverage_note.setWordWrap(True)
        layout.addWidget(coverage_note)
        self.scoring_status = QLabel()
        self.scoring_status.setWordWrap(True)
        layout.addWidget(self.scoring_status)

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
            "Band of Error\n(+/-)",
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
            item.setBackground(QColor(MULLEN_SCALE_BACKGROUND_COLOR))
            item.setForeground(QColor(MULLEN_SCALE_TEXT_COLOR))

            scale_font = QFont(item.font())
            scale_font.setWeight(MULLEN_SCALE_FONT_WEIGHT)
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
        self.score_table.setStyleSheet(
            themed_stylesheet(
                MULLEN_SCORE_TABLE_STYLESHEET,
                DARK_MULLEN_STYLESHEET,
                self.preferences["theme"],
            )
        )

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
        for inputs in (
            self.t_score_inputs,
            self.error_inputs,
            self.percentile_inputs,
            self.category_inputs,
        ):
            for field in inputs.values():
                field.setReadOnly(True)
        for field in (
            self.date_of_birth_input,
            self.assessment_date_input,
            *self.raw_score_inputs.values(),
        ):
            field.textChanged.connect(self.recalculate_scores)
        self.confidence_combo.currentIndexChanged.connect(self.recalculate_scores)
        self.age_calculation_combo.currentIndexChanged.connect(self.recalculate_scores)

    def use_overview_dob(self) -> None:
        patient = get_patient(self.patient_id) or {}
        self.date_of_birth_input.setText(
            format_date(patient.get("date_of_birth"), self.date_format)
        )

    def collect_context(self) -> dict:
        if not self.date_of_birth_input.text().strip():
            raise MullenScoringError(
                "Save the date of birth in Overview, then choose Use Overview DOB."
            )
        if not self.assessment_date_input.text().strip():
            raise MullenScoringError(
                f"Enter the assessment date as {self.date_format}."
            )
        birthday = parse_date(self.date_of_birth_input.text(), self.date_format)
        tested_on = parse_date(self.assessment_date_input.text(), self.date_format)
        confidence = self.confidence_combo.currentData()
        convention = self.age_calculation_combo.currentData()
        if confidence is None:
            raise MullenScoringError("Select a confidence level: 90% or 95%.")
        if convention is None:
            raise MullenScoringError(
                "Select the age calculation convention specified by your handbook."
            )
        months, days = calculate_age(birthday, tested_on, convention=convention)
        self.age_label.setText(f"Age at assessment: {months} months, {days} days")
        return {
            "assessment_date": tested_on,
            "scoring_date_of_birth": birthday,
            "confidence_level": confidence,
            "age_calculation": convention,
        }

    def _context_status(self) -> tuple[dict | None, str]:
        self.age_label.clear()
        try:
            return self.collect_context(), ""
        except ValueError as exc:
            return None, str(exc)

    def recalculate_scores(self, *_args) -> list[str]:
        if self._loading:
            return []
        context, context_error = self._context_status()
        errors = [context_error] if context_error else []
        outputs = {
            "t_score": self.t_score_inputs,
            "band_of_error": self.error_inputs,
            "percentile_rank": self.percentile_inputs,
            "descriptive_category": self.category_inputs,
        }
        for row, (domain, label) in enumerate(self.scales):
            for inputs in outputs.values():
                inputs[row].clear()
            raw_text = self.raw_score_inputs[row].text().strip()
            if not raw_text or context is None:
                continue
            try:
                result = auto_score(
                    int(raw_text),
                    context["scoring_date_of_birth"],
                    domain=domain,
                    assessment_date=context["assessment_date"],
                    confidence_level=context["confidence_level"],
                    age_calculation=context["age_calculation"],
                )
            except ValueError as exc:
                errors.append(f"{' '.join(label.split())}: {exc}")
                continue
            for field, inputs in outputs.items():
                inputs[row].setText(str(result[field]))
        self.scoring_status.setText(
            "\n".join(errors)
            if errors
            else "Scores update automatically. Band of error is shown as a +/- width."
        )
        return errors

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
        context = get_mullen_assessment_context(self.patient_id)
        patient = get_patient(self.patient_id) or {}

        input_fields = {
            "raw_score": self.raw_score_inputs,
            "t_score": self.t_score_inputs,
            "band_of_error": self.error_inputs,
            "percentile_rank": self.percentile_inputs,
            "descriptive_category": self.category_inputs,
            "age_equivalence": self.age_equivalent_inputs,
        }

        self._loading = True
        try:
            birthday = context.get("scoring_date_of_birth") or patient.get(
                "date_of_birth"
            )
            self.date_of_birth_input.setText(format_date(birthday, self.date_format))
            self.assessment_date_input.setText(
                format_date(context.get("assessment_date"), self.date_format)
            )
            self.confidence_combo.setCurrentIndex(
                max(0, self.confidence_combo.findData(context.get("confidence_level")))
            )
            self.age_calculation_combo.setCurrentIndex(
                max(
                    0,
                    self.age_calculation_combo.findData(context.get("age_calculation")),
                )
            )
            for row, (domain, _scale_label) in enumerate(self.scales):
                scores = data.get(domain, {})
                for field, row_inputs in input_fields.items():
                    value = scores.get(field)
                    row_inputs[row].setText("" if value is None else str(value))
        finally:
            self._loading = False
        _, error = self._context_status()
        if birthday and birthday != patient.get("date_of_birth"):
            error = "Overview DOB differs from this saved assessment. Choose Use Overview DOB to recalculate with it."
        self.scoring_status.setText(
            error
            or "Saved scores loaded. Editing raw scores or scoring options recalculates results."
        )

    def has_answers(self) -> bool:
        return bool(
            self.assessment_date_input.text().strip()
            or self.confidence_combo.currentData() is not None
            or self.age_calculation_combo.currentData() is not None
            or any(field.text().strip() for field in self.raw_score_inputs.values())
            or any(field.text().strip() for field in self.age_equivalent_inputs.values())
        )

    def save(self, *, show_confirmation=True) -> bool:
        errors = self.recalculate_scores()
        if errors:
            QMessageBox.warning(
                self, "Unable to score Mullen assessment", "\n".join(errors)
            )
            return False
        try:
            data = self.collect_data()
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Mullen Score",
                "Please enter numbers in every score field except "
                "Descriptive Category.",
            )
            return False

        save_mullen_assessment(self.patient_id, data, context=self.collect_context())
        if show_confirmation:
            QMessageBox.information(
                self,
                "Saved",
                "Mullen scores saved successfully.",
            )
        return True

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
