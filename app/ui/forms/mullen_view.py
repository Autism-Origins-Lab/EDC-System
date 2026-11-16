from PySide6.QtCore import QRegularExpression, QSignalBlocker, Qt, Signal
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
    list_mullen_assessments,
    save_mullen_assessment,
)
from app.database.repositories.patients import get_patient
from app.services.mullen_scoring import MullenScoringError, auto_score, calculate_age
from app.services.preferences import DATE_FORMAT, format_date, load_preferences, parse_date
from app.ui.components.date_input import DateInput
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
    summary_loaded = Signal()

    def __init__(self, patient_id: int, preferences: dict | None = None):
        super().__init__()

        self.patient_id = patient_id
        self._loading = False
        self.assessment_id = None
        self._initialized = False
        self._new_requested = False
        self._saved_state = ()
        self.save_handler = None
        self.preferences = preferences or load_preferences()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Mullen Score Summary")
        title.setObjectName("PageTitle")
        title.setStyleSheet(MULLEN_TITLE_STYLESHEET)

        layout.addWidget(title)

        subtitle = QLabel(
            "Enter raw scores to fill T scores, error widths, percentiles, and categories. "
            "Automatic scoring covers birth through 3 months, 30 days."
        )
        subtitle.setObjectName("Muted")
        subtitle.setStyleSheet(MULLEN_SUBTITLE_STYLESHEET)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        summary_row = QHBoxLayout()
        summary_row.addWidget(QLabel("Summary"))
        self.assessment_combo = QComboBox()
        self.assessment_combo.setAccessibleName("Mullen summary")
        summary_row.addWidget(self.assessment_combo, 1)
        self.new_summary_button = QPushButton("New summary")
        self.new_summary_button.clicked.connect(self.new_summary)
        summary_row.addWidget(self.new_summary_button)
        layout.addLayout(summary_row)

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

        self.assessment_date_input = DateInput()
        context_form.addRow("Date completed (required)", self.assessment_date_input)
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
            "Automatic scoring is available from birth through 3 months, 30 days. "
            "Leave raw scores blank for scales not administered."
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
            raw_input = self.create_input(placeholder="Not administered", numeric=True)
            raw_input.setMinimumWidth(raw_input.fontMetrics().horizontalAdvance("Not administered") + 40)
            raw_input.setToolTip("Leave blank if not administered. Enter 0 for a raw score of zero.")
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
            1, QHeaderView.ResizeMode.Fixed
        )
        self.score_table.setColumnWidth(1, self.raw_score_inputs[0].minimumWidth() + 44)
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
        self.save_button.clicked.connect(lambda: self.save())

        self.save_button.setMinimumHeight(42)
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.load_existing_data()
        self.assessment_combo.currentIndexChanged.connect(self._select_summary)
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
        self.date_of_birth_input.setText(format_date(patient.get("date_of_birth")))

    def collect_context(self) -> dict:
        has_raw_scores = any(field.text().strip() for field in self.raw_score_inputs.values())
        if has_raw_scores and not self.date_of_birth_input.text().strip():
            raise MullenScoringError(
                "Save the date of birth in Overview, then choose Use Overview DOB."
            )
        if not self.assessment_date_input.text().strip():
            raise MullenScoringError(f"Enter Date completed as {DATE_FORMAT}.")
        birthday = (
            parse_date(self.date_of_birth_input.text())
            if self.date_of_birth_input.text().strip() else None
        )
        tested_on = parse_date(self.assessment_date_input.text())
        confidence = self.confidence_combo.currentData()
        convention = self.age_calculation_combo.currentData()
        if birthday is not None and tested_on < birthday:
            raise MullenScoringError("Assessment date cannot precede date of birth.")
        if has_raw_scores and confidence is None:
            raise MullenScoringError("Select a confidence level: 90% or 95%.")
        if has_raw_scores and convention is None:
            raise MullenScoringError(
                "Select the age calculation convention specified by your handbook."
            )
        if birthday is not None and convention is not None:
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

    def input_widgets(self) -> list:
        return [
            self.date_of_birth_input, self.assessment_date_input,
            self.confidence_combo, self.age_calculation_combo,
            *self.raw_score_inputs.values(), *self.t_score_inputs.values(),
            *self.error_inputs.values(), *self.percentile_inputs.values(),
            *self.category_inputs.values(), *self.age_equivalent_inputs.values(),
        ]

    def input_state(self) -> tuple:
        return (
            ("summary", (self.assessment_id, self._new_requested)),
            *(("combo", field.currentData()) if isinstance(field, QComboBox)
              else ("line", field.text()) for field in self.input_widgets()),
        )

    @property
    def saved_input_state(self) -> tuple:
        return self._saved_state

    def has_unsaved_changes(self) -> bool:
        return self.input_state() != self._saved_state

    def restore_input_state(self, state: tuple) -> None:
        self._loading = True
        try:
            self.assessment_id, self._new_requested = state[0][1]
            for field, (_kind, value) in zip(self.input_widgets(), state[1:], strict=True):
                if isinstance(field, QComboBox):
                    field.setCurrentIndex(max(0, field.findData(value)))
                else:
                    field.setText(value)
            self._refresh_selector()
        finally:
            self._loading = False

    def _refresh_selector(self) -> None:
        with QSignalBlocker(self.assessment_combo):
            self.assessment_combo.clear()
            summaries = list_mullen_assessments(self.patient_id)
            for summary in summaries:
                completed = format_date(summary["assessment_date"]) or "Date not recorded"
                self.assessment_combo.addItem(
                    f"Mullen #{summary['assessment_number']} — {completed}", summary["id"]
                )
            if self.assessment_id is None:
                self.assessment_combo.addItem("New summary (unsaved)", None)
            self.assessment_combo.setCurrentIndex(
                self.assessment_combo.findData(self.assessment_id)
            )

    def _confirm_pending_changes(self) -> bool:
        if not self.has_unsaved_changes():
            return True
        choice = QMessageBox.question(
            self, "Unsaved Mullen summary", "Save changes to this summary before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        if choice == QMessageBox.StandardButton.Save:
            return self.save_handler() if self.save_handler else self.save()
        return choice == QMessageBox.StandardButton.Discard

    def _select_summary(self, index: int) -> None:
        if self._loading:
            return
        target_id = self.assessment_combo.itemData(index)
        if target_id == self.assessment_id:
            return
        # Keep the selected label consistent if switching is cancelled or saving fails.
        with QSignalBlocker(self.assessment_combo):
            self.assessment_combo.setCurrentIndex(self.assessment_combo.findData(self.assessment_id))
        if self._confirm_pending_changes():
            self.assessment_id = target_id
            self._new_requested = False
            self._load_summary()

    def new_summary(self) -> None:
        if not self._confirm_pending_changes():
            return
        self.assessment_id = None
        self._new_requested = False
        self._load_summary()
        self._new_requested = True
        self.summary_loaded.emit()
        self.assessment_date_input.setFocus()

    def load_existing_data(self) -> None:
        summaries = list_mullen_assessments(self.patient_id)
        if not self._initialized or (
            self.assessment_id is None and not self._new_requested and not self.has_answers()
        ):
            self.assessment_id = summaries[0]["id"] if summaries else None
        self._initialized = True
        self._load_summary()

    def _load_summary(self) -> None:
        data = get_mullen_assessment(self.patient_id, self.assessment_id) if self.assessment_id else {}
        context = (
            get_mullen_assessment_context(self.patient_id, self.assessment_id)
            if self.assessment_id else {}
        )
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
            self.date_of_birth_input.setText(format_date(birthday))
            self.assessment_date_input.setText(format_date(context.get("assessment_date")))
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
            self._refresh_selector()
        finally:
            self._loading = False
        _, error = self._context_status()
        if birthday and birthday != patient.get("date_of_birth"):
            error = "Overview DOB differs from this saved assessment. Choose Use Overview DOB to recalculate with it."
        self.scoring_status.setText(
            error
            or "Saved scores loaded. Editing raw scores or scoring options recalculates results."
        )
        self._new_requested = False
        self._saved_state = self.input_state()
        self.summary_loaded.emit()

    def has_answers(self) -> bool:
        return bool(
            self.assessment_date_input.text().strip()
            or self.confidence_combo.currentData() is not None
            or self.age_calculation_combo.currentData() is not None
            or any(field.text().strip() for field in self.raw_score_inputs.values())
            or any(field.text().strip() for field in self.age_equivalent_inputs.values())
        )

    def save(self, *, show_confirmation=True) -> bool:
        # An untouched optional section creates no summary. Explicit new summaries
        # and existing summaries must pass date validation even with no scores.
        if self.assessment_id is None and not self._new_requested and not self.has_answers():
            return True
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

        self.assessment_id = save_mullen_assessment(
            self.patient_id, data, context=self.collect_context(), assessment_id=self.assessment_id
        )
        self._new_requested = False
        if show_confirmation:
            self.load_existing_data()
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
