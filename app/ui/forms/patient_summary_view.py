from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.forms import (
    get_mullen_assessment,
    get_mullen_assessment_context,
    get_telephone_screening,
    save_telephone_screening,
)
from app.database.repositories.patients import get_patient
from app.database.repositories.videos import list_patient_videos
from app.services.preferences import format_date
from app.ui.components.yes_no_input import YesNoInput


class PatientSummaryView(QWidget):
    """Review saved answers without changing blanks into database values."""

    def __init__(self, patient_id, form_views, section_titles, date_format):
        super().__init__()
        self.patient_id = patient_id
        self.form_views = form_views
        self.section_titles = section_titles
        self.date_format = date_format
        self.answers = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self.screener_input = QLineEdit()
        self.screener_input.setPlaceholderText("Enter the screener's full name")
        self.screener_input.setAccessibleName("Screener name, required")
        form.addRow("Screener name (required)", self.screener_input)
        layout.addLayout(form)
        note = QLabel(
            "Review the saved answers below. Empty answers are shown as N/A. "
            "Use Back to make changes before marking the form as complete."
        )
        note.setObjectName("WorkspaceMuted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.required_note = QLabel("Enter a screener name to complete this form.")
        self.required_note.setObjectName("WorkspaceMuted")
        layout.addWidget(self.required_note)
        self.answer_tree = QTreeWidget()
        self.answer_tree.setObjectName("SummaryAnswers")
        self.answer_tree.setHeaderLabels(["Question", "Answer"])
        self.answer_tree.setAccessibleName("Saved form answers")
        self.answer_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.answer_tree.setWordWrap(True)
        self.answer_tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.answer_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        self.answer_tree.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.answer_tree.setColumnWidth(0, 360)
        layout.addWidget(self.answer_tree, 1)
        self.screener_input.textChanged.connect(self._update_screener)
        self.load_existing_data()

    @staticmethod
    def display_answer(value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return "N/A"
        return str(value)

    @staticmethod
    def _form_answers(view):
        answers = []
        for form in view.findChildren(QFormLayout):
            group = form.parentWidget()
            prefix = f"{group.title()} / " if isinstance(group, QGroupBox) else ""
            for row in range(form.rowCount()):
                item = form.itemAt(row, QFormLayout.ItemRole.FieldRole)
                field = item.widget() if item else None
                label = form.labelForField(field) if field else None
                question = label.text() if isinstance(label, QLabel) else ""
                if isinstance(field, YesNoInput):
                    value = {None: None, 1: "Yes", 0: "No"}[field.value()]
                elif isinstance(field, QCheckBox):
                    question = question or field.text()
                    risk_inputs = (
                        getattr(view, "high_risk_checkbox", None),
                        getattr(view, "low_risk_checkbox", None),
                    )
                    if field in risk_inputs and not any(
                        checkbox.isChecked() for checkbox in risk_inputs if checkbox is not None
                    ):
                        value = None
                    else:
                        value = "Yes" if field.isChecked() else "No"
                elif isinstance(field, QLineEdit):
                    value = field.text()
                elif isinstance(field, QTextEdit):
                    value = field.toPlainText()
                elif isinstance(field, QComboBox):
                    value = field.currentText()
                else:
                    continue
                answers.append((prefix + question, value))
        return answers

    def load_existing_data(self):
        screening = get_telephone_screening(self.patient_id) or {}
        self.screener_input.setText(screening.get("screener") or "")
        self.refresh_answers()

    def refresh_answers(self):
        self.answers = []
        for index, view in enumerate(self.form_views):
            if index == 6:
                context = get_mullen_assessment_context(self.patient_id)
                rows = [
                    (
                        "Date of birth used",
                        format_date(
                            context.get("scoring_date_of_birth"), self.date_format
                        ),
                    ),
                    (
                        "Assessment date",
                        format_date(context.get("assessment_date"), self.date_format),
                    ),
                    (
                        "Confidence level",
                        f"{context['confidence_level']}%"
                        if context.get("confidence_level")
                        else None,
                    ),
                    (
                        "Age calculation",
                        {
                            "calendar": "Calendar months",
                            "30_day_borrow": "30-day borrowing",
                        }.get(context.get("age_calculation")),
                    ),
                ]
                scores = get_mullen_assessment(self.patient_id)
                fields = (
                    ("raw_score", "Raw score"),
                    ("t_score", "T score"),
                    ("band_of_error", "Band of error (+/-)"),
                    ("percentile_rank", "Percentile rank"),
                    ("descriptive_category", "Descriptive category"),
                    ("age_equivalence", "Age equivalent"),
                )
                for domain, label in view.scales:
                    for field, title in fields:
                        rows.append(
                            (
                                f"{' '.join(label.split())} / {title}",
                                scores.get(domain, {}).get(field),
                            )
                        )
            elif index == 7:
                videos = list_patient_videos(self.patient_id)
                rows = []
                for number, video in enumerate(videos, 1):
                    rows.extend(
                        [
                            (f"Video {number} / Title", video.get("title")),
                            (f"Video {number} / File path", video.get("file_path")),
                        ]
                    )
                if not rows:
                    rows = [("Video references", None)]
            else:
                rows = self._form_answers(view)
                if index == 0:
                    risk = (get_patient(self.patient_id) or {}).get("risk")
                    rows.append(("Familial risk", {1: "High", 0: "Low"}.get(risk)))
            self.answers.append(
                (
                    self.section_titles[index],
                    [
                        (question, self.display_answer(value))
                        for question, value in rows
                    ],
                )
            )

        self.answer_tree.clear()
        for title, answers in self.answers:
            section = QTreeWidgetItem(self.answer_tree, [title, ""])
            font = section.font(0)
            font.setBold(True)
            section.setFont(0, font)
            for question, answer in answers:
                item = QTreeWidgetItem(section, [question, answer])
                item.setToolTip(1, answer)
        self.answer_tree.expandAll()
        self._update_screener()

    def _update_screener(self, *_args):
        name = self.screener_input.text().strip()
        self.required_note.setVisible(not bool(name))

    def save(self, *, show_confirmation=True):
        save_telephone_screening(
            self.patient_id, {"screener": self.screener_input.text().strip()}
        )
        return True
