from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.queries.forms import (
    HIGH_RISK,
    LOW_RISK,
    familial_risk,
    get_family_medical_history,
    list_siblings,
    save_family_medical_history,
    save_siblings,
)
from app.ui.widgets.conditional_section import ConditionalSection
from app.ui.widgets.siblings_table import SiblingsTable
from app.ui.widgets.yes_no_question import YES, YesNoQuestion

# Wording follows page 4 of the paper Telephone Screener so RAs can read it aloud.

DISQUALIFIER_QUESTIONS = {
    "parent_autism": (
        "2a. Either mother or father been diagnosed with an Autism Spectrum Disorder?",
        "For this screening, ask about autism, Asperger's or PDD-NOS diagnoses.",
    ),
    "parent_schizophrenia": (
        "2b. Either mother or father been diagnosed with schizophrenia?",
        None,
    ),
    "parent_learning_disability": (
        "2c. Either mother or father been diagnosed with learning and/or intellectual disability?",
        "For this screening, 2c means intellectual disability, and it's a disqualifier.",
    ),
    "parent_substance_abuse": (
        "2d. Either mother or father has a history of substance abuse?",
        (
            'Alcohol and/or street or prescription drugs. "History" means more than '
            "6 months and recurring. A disqualifier."
        ),
    ),
}

SIBLING_TYPE_OPTIONS = {
    "full": "Full biological sibling",
    "half": "Half sibling",
    "adopted": "Adopted sibling",
}

def sibling_section(condition_key: str, condition_name: str, question: str) -> ConditionalSection:
    """Questions 4 and 5 are identical apart from the condition."""
    options = {
        f"sibling_{condition_key}_{kind}": label for kind, label in SIBLING_TYPE_OPTIONS.items()
    }
    options[f"sibling_{condition_key}_multiple"] = f"More than 1 sibling with {condition_name}"
    return ConditionalSection(
        key=f"sibling_{condition_key}",
        label=question,
        options=options,
        options_heading="Check if:",
    )


class FamilyMedicalHistoryView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id

        # Colors follow the system palette (like the other form tabs), so the
        # page is dark gray in dark mode. Only the warning accents are fixed reds.
        self.setObjectName("FamilyMedicalHistoryView")
        self.setStyleSheet(
            """
            QLabel#SectionHeading, QLabel#FollowUpLabel { color: palette(window-text); }
            QLabel#SectionHeading { font-weight: 600; }
            QLabel#SectionHelp { color: #9ca3af; font-size: 12px; font-style: italic; }
            QLabel#SectionHeading:disabled, QLabel#FollowUpLabel:disabled,
            QLabel#SectionHelp:disabled { color: #6b7280; }
            QFrame#DisqualifierBox {
                background: rgba(190, 90, 90, 0.07);
                border: 1px solid rgba(190, 90, 90, 0.25);
                border-left: 3px solid #b45f5f;
                border-radius: 6px;
            }
            QLabel#DisqualifierTag { color: #d79a9a; font-weight: 600; }
            QLabel#IneligibleBanner {
                background: #5a2e2e;
                border: 1px solid #8a4545;
                color: #f3dede;
                border-radius: 6px;
                font-weight: 600;
                padding: 12px;
            }
            QLabel#RiskSuggestion {
                color: palette(window-text);
                border: 1px solid palette(mid);
                border-left: 3px solid #1d63ed;
                border-radius: 6px;
                padding: 10px 12px;
            }
            """
        )

        outer_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # --- Question 1, with a multi-line description box shown on "Yes" ---
        self.family_psychiatric_question = YesNoQuestion(
            "1. Have any of the child's relatives (father, mother, full biological siblings) "
            "ever been diagnosed with a psychiatric illness by a mental health professional?"
        )
        self.family_psychiatric_description_input = QTextEdit()
        self.family_psychiatric_description_input.setFixedHeight(80)
        # Text boxes ask for extra height by default; without this, the
        # spare space on the page ends up around this question.
        self.family_psychiatric_description_input.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self.family_psychiatric_panel = QWidget()
        panel_layout = QVBoxLayout(self.family_psychiatric_panel)
        panel_layout.setContentsMargins(16, 0, 0, 0)
        panel_layout.setSpacing(4)
        description_label = QLabel("If yes, what was the diagnosis? Briefly describe the illness.")
        description_label.setObjectName("FollowUpLabel")
        description_label.setWordWrap(True)
        panel_layout.addWidget(description_label)
        panel_layout.addWidget(self.family_psychiatric_description_input)
        self.family_psychiatric_panel.setVisible(False)
        self.family_psychiatric_question.answered.connect(
            self._update_family_psychiatric_panel
        )

        layout.addWidget(self.family_psychiatric_question)
        layout.addWidget(self.family_psychiatric_panel)

        # --- Question 2a-2d: disqualifiers ---
        disqualifier_box = QFrame()
        disqualifier_box.setObjectName("DisqualifierBox")
        disqualifier_layout = QVBoxLayout(disqualifier_box)
        disqualifier_layout.setContentsMargins(14, 10, 10, 10)
        disqualifier_layout.setSpacing(12)

        heading = QLabel("2. Check answers in #1 and ask to clarify whether:")
        heading.setObjectName("SectionHeading")
        tag = QLabel("Disqualifiers: any Yes makes the baby ineligible.")
        tag.setObjectName("DisqualifierTag")
        disqualifier_layout.addWidget(heading)
        disqualifier_layout.addWidget(tag)

        self.disqualifier_questions: dict[str, YesNoQuestion] = {}
        for key, (text, help_text) in DISQUALIFIER_QUESTIONS.items():
            question = YesNoQuestion(text, help_text=help_text)
            question.answered.connect(self._update_eligibility)
            disqualifier_layout.addWidget(question)
            self.disqualifier_questions[key] = question

        layout.addWidget(disqualifier_box)

        self.ineligible_banner = QLabel(
            "Ineligible: the new baby is not eligible. Stop asking questions "
            "and thank the person for their time."
        )
        self.ineligible_banner.setObjectName("IneligibleBanner")
        self.ineligible_banner.setWordWrap(True)
        self.ineligible_banner.setVisible(False)
        layout.addWidget(self.ineligible_banner)

        # --- Question 3 onward, in one container so a disqualifier can disable it all ---
        self.after_disqualifiers = QWidget()
        after_layout = QVBoxLayout(self.after_disqualifiers)
        after_layout.setContentsMargins(0, 0, 0, 0)
        after_layout.setSpacing(18)

        self.has_siblings_question = YesNoQuestion(
            "3. Does your child have any siblings?",
            help_text="If yes, ask for each sibling's name and age.",
        )
        self.has_siblings_question.answered.connect(self._update_siblings_section)
        after_layout.addWidget(self.has_siblings_question)

        # Questions 4-5 and the siblings table only show if Q3 is Yes
        self.siblings_section = QWidget()
        siblings_layout = QVBoxLayout(self.siblings_section)
        siblings_layout.setContentsMargins(0, 0, 0, 0)
        siblings_layout.setSpacing(18)

        self.sibling_autism_section = sibling_section(
            "autism",
            "ASD",
            "4. Has either sister or brother been diagnosed with an Autism Spectrum Disorder?",
        )
        self.sibling_adhd_section = sibling_section(
            "adhd",
            "ADHD",
            "5. Has either sister or brother been diagnosed with an "
            "Attention Deficit/Hyperactivity Disorder?",
        )
        siblings_layout.addWidget(self.sibling_autism_section)
        siblings_layout.addWidget(self.sibling_adhd_section)

        siblings_heading = QLabel("Siblings")
        siblings_heading.setObjectName("SectionHeading")
        siblings_help = QLabel(
            "Add one row per sibling. Ask whether each one has the same biological "
            "father and the same biological mother as this child (this replaces paper "
            "question 6). Leave a dropdown blank if the caller doesn't know."
        )
        siblings_help.setObjectName("SectionHelp")
        siblings_help.setWordWrap(True)
        self.siblings_table = SiblingsTable()
        siblings_layout.addWidget(siblings_heading)
        siblings_layout.addWidget(siblings_help)
        siblings_layout.addWidget(self.siblings_table)
        self.siblings_section.setVisible(False)
        after_layout.addWidget(self.siblings_section)

        layout.addWidget(self.after_disqualifiers)

        # Suggested risk from the answers above. The RA still sets it on the
        # Telephone Screening tab, so nothing here changes risk by itself.
        self.risk_suggestion = QLabel()
        self.risk_suggestion.setObjectName("RiskSuggestion")
        self.risk_suggestion.setWordWrap(True)
        layout.addWidget(self.risk_suggestion)

        # Refresh the suggestion whenever an answer it depends on changes
        for question in (
            self.family_psychiatric_question,
            self.has_siblings_question,
            self.sibling_autism_section.question,
            self.sibling_adhd_section.question,
        ):
            question.answered.connect(self._update_risk_suggestion)
        self.siblings_table.changed.connect(self._update_risk_suggestion)

        save_button = QPushButton("Save Family Medical History")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save)

        layout.addWidget(save_button)
        layout.addStretch()
        scroll_area.setWidget(page)
        outer_layout.addWidget(scroll_area)

        self.load_existing_data()

    # --- Reacting to answers ---

    def _update_family_psychiatric_panel(self, value: int | None) -> None:
        self.family_psychiatric_panel.setVisible(value == YES)

    def _update_siblings_section(self, value: int | None) -> None:
        self.siblings_section.setVisible(value == YES)

    def has_disqualifier(self) -> bool:
        return any(question.value() == YES for question in self.disqualifier_questions.values())

    def _update_eligibility(self, _value: int | None = None) -> None:
        # TODO: Ask coordinator: should a disqualifier also set telephone screening
        # eligibility to No?
        ineligible = self.has_disqualifier()
        self.ineligible_banner.setVisible(ineligible)
        # Disabling the container disables every widget inside it.
        # Saving is still allowed, so the save button stays outside it.
        self.after_disqualifiers.setEnabled(not ineligible)
        self._update_risk_suggestion()

    def _update_risk_suggestion(self, *_args) -> None:
        # Risk doesn't matter once the baby is ineligible
        if self.has_disqualifier():
            self.risk_suggestion.setVisible(False)
            return

        risk, reason = familial_risk(self.collect_data(), self.collect_siblings())
        if risk == HIGH_RISK:
            heading = "Suggested familial risk: High"
        elif risk == LOW_RISK:
            heading = "Suggested familial risk: Low"
        else:
            heading = "Suggested familial risk: not determined"

        text = f"<b>{heading}</b><br>{reason}"
        if risk is not None:
            text += "<br>Tick High or Low familial risk on the Telephone Screening tab."
        self.risk_suggestion.setText(text)
        self.risk_suggestion.setVisible(True)

    # --- Loading and saving ---

    def load_existing_data(self) -> None:
        data = get_family_medical_history(self.patient_id) or {}

        self.family_psychiatric_question.set_value(data.get("family_psychiatric"))
        self.family_psychiatric_description_input.setPlainText(
            data.get("family_psychiatric_description") or ""
        )
        for key, question in self.disqualifier_questions.items():
            question.set_value(data.get(key))
        self.has_siblings_question.set_value(data.get("has_siblings"))
        self.sibling_autism_section.set_data(data)
        self.sibling_adhd_section.set_data(data)
        self.siblings_table.set_siblings(list_siblings(self.patient_id))

        self._update_eligibility()

    def collect_data(self) -> dict:
        family_psychiatric = self.family_psychiatric_question.value()
        has_siblings = self.has_siblings_question.value()

        data = {
            "family_psychiatric": family_psychiatric,
            "family_psychiatric_description": (
                self.family_psychiatric_description_input.toPlainText().strip()
                if family_psychiatric == YES
                else ""
            ),
        }
        for key, question in self.disqualifier_questions.items():
            data[key] = question.value()
        data["has_siblings"] = has_siblings

        # Questions 4-5 are only asked when there are siblings
        siblings_asked = has_siblings == YES
        data.update(self.sibling_autism_section.get_data(asked=siblings_asked))
        data.update(self.sibling_adhd_section.get_data(asked=siblings_asked))
        return data

    def collect_siblings(self) -> list[dict]:
        # No siblings were asked about unless Q3 is Yes
        if self.has_siblings_question.value() != YES:
            return []
        return self.siblings_table.collect_siblings()

    def save(self) -> None:
        save_family_medical_history(self.patient_id, self.collect_data())
        save_siblings(self.patient_id, self.collect_siblings())
        QMessageBox.information(self, "Saved", "Family medical history saved successfully.")
