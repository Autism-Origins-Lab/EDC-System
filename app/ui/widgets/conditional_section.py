from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.yes_no_question import YES, YesNoQuestion


class ConditionalSection(QWidget):
    """A Yes/No question that reveals a group of follow-up questions on "Yes".

    Every key passed in is a database column name, so get_data() and set_data()
    line up directly with the rows the query functions read and write.
    """

    def __init__(
        self,
        key: str,
        label: str,
        options: dict[str, str] | None = None,
        other_key: str | None = None,
        text_fields: dict[str, str] | None = None,
        help_text: str | None = None,
        options_heading: str | None = None,
    ):
        super().__init__()
        self.key = key
        self.label = label
        self.other_key = other_key

        # The parent question (the "light switch")
        self.question = YesNoQuestion(label, help_text=help_text)

        # The container that holds every sub-option (the "lamp")
        self.panel = QFrame()
        self.panel.setObjectName("SubOptions")
        # Use the system text color so the panel matches dark and light mode
        self.panel.setStyleSheet(
            """
            QFrame#SubOptions QCheckBox, QFrame#SubOptions QLabel { color: palette(window-text); }
            QFrame#SubOptions QCheckBox:disabled, QFrame#SubOptions QLabel:disabled { color: #6b7280; }
            """
        )
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(16, 4, 0, 4)
        panel_layout.setSpacing(6)

        # Optional heading above the sub-options, like "Check if:"
        if options_heading:
            panel_layout.addWidget(QLabel(options_heading))

        # One sub-checkbox per option
        self.option_checkboxes: dict[str, QCheckBox] = {}
        for option_key, option_label in (options or {}).items():
            checkbox = QCheckBox(option_label)
            panel_layout.addWidget(checkbox)
            self.option_checkboxes[option_key] = checkbox

        # Optional "Other" checkbox with its own text box
        self.other_checkbox: QCheckBox | None = None
        self.other_input: QLineEdit | None = None
        if other_key:
            self.other_checkbox = QCheckBox("Other (please specify)")
            self.other_input = QLineEdit()
            self.other_input.setPlaceholderText("Type the condition")
            self.other_input.setAccessibleName(f"{label}: other, please specify")
            self.other_input.setEnabled(False)
            self.other_checkbox.toggled.connect(self.other_input.setEnabled)
            panel_layout.addWidget(self.other_checkbox)
            panel_layout.addWidget(self.other_input)

        # Optional free-text boxes, each with a visible label
        self.text_inputs: dict[str, QLineEdit] = {}
        if text_fields:
            text_form = QFormLayout()
            for field_key, field_label in text_fields.items():
                line_edit = QLineEdit()
                text_form.addRow(field_label, line_edit)
                self.text_inputs[field_key] = line_edit
            panel_layout.addLayout(text_form)

        # Stack the parent question on top of the panel
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.question)
        layout.addWidget(self.panel)

        # The "wire": answering Yes shows the panel; No or blank hides it
        self.panel.setVisible(False)
        self.question.answered.connect(self._show_panel_if_yes)

    def _show_panel_if_yes(self, value: int | None) -> None:
        self.panel.setVisible(value == YES)

    def get_data(self, asked: bool = True) -> dict:
        # asked=False means the whole question is hidden, so save it as unanswered
        answer = self.question.value() if asked else None  # 1, 0, or None
        is_yes = answer == YES
        data = {self.key: answer}

        # Hidden sub-options save 0, so a stale tick never sneaks through
        for option_key, checkbox in self.option_checkboxes.items():
            data[option_key] = int(is_yes and checkbox.isChecked())

        if self.other_key:
            other_checked = is_yes and self.other_checkbox.isChecked()
            data[self.other_key] = int(other_checked)
            data[f"{self.other_key}_description"] = (
                self.other_input.text().strip() if other_checked else ""
            )

        for field_key, line_edit in self.text_inputs.items():
            data[field_key] = line_edit.text().strip() if is_yes else ""

        return data

    def set_data(self, data: dict) -> None:
        # set_value() emits "answered", which shows or hides the panel
        self.question.set_value(data.get(self.key))

        for option_key, checkbox in self.option_checkboxes.items():
            checkbox.setChecked(bool(data.get(option_key)))

        if self.other_key:
            self.other_checkbox.setChecked(bool(data.get(self.other_key)))
            self.other_input.setText(data.get(f"{self.other_key}_description") or "")

        for field_key, line_edit in self.text_inputs.items():
            line_edit.setText(data.get(field_key) or "")

    def validation_errors(self) -> list[str]:
        data = self.get_data()
        if data[self.key] != YES:
            return []

        errors = []
        choice_keys = list(self.option_checkboxes)
        if self.other_key:
            choice_keys.append(self.other_key)
        if choice_keys and not any(data[choice_key] for choice_key in choice_keys):
            errors.append(f'"{self.label}" is answered Yes, but nothing underneath it is selected.')

        if self.other_key and data[self.other_key] and not data[f"{self.other_key}_description"]:
            errors.append(f'"{self.label}": "Other" is checked, so please type what it is.')

        return errors
