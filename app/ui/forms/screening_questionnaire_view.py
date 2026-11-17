from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories.forms import (
    get_screening_questionnaire,
    save_screening_questionnaire,
)
from app.services.preferences import DATE_FORMAT, format_date, parse_date
from app.ui.components.contact_inputs import (
    US_STATES,
    ChoiceInput,
    PhoneInput,
    TimeOfDayInput,
    digits_only,
)
from app.ui.components.date_input import DateInput
from app.ui.components.yes_no_input import YesNoInput

SEX_OPTIONS = [(sex, sex) for sex in ("Female", "Male", "Other", "Prefer not to answer")]
ZIP_CODE_DIGITS = 5


class ScreeningQuestionnaireView(QWidget):
    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id

        outer_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)


        self.parent_name_input = QLineEdit()
        self.child_name_input = QLineEdit()
        self.date_of_birth_input = DateInput()
        self.sex_combo = ChoiceInput(SEX_OPTIONS)
        self.state_input = ChoiceInput(US_STATES)
        self.zip_code_input = QLineEdit()
        self.zip_code_input.setValidator(digits_only(ZIP_CODE_DIGITS))
        self.home_phone_input = PhoneInput()
        self.work_phone_input = PhoneInput()
        self.best_time_to_call_input = TimeOfDayInput()
        self.biological_mother_input = YesNoInput("Mother listed is biological mother")
        self.biological_father_input = YesNoInput("Father listed is biological father")
        self.research_participation_input = YesNoInput("Family has participated in research")

        rows = [
            ("parent_name", "Parent Name", self.parent_name_input),
            ("child_name", "Child Name", self.child_name_input),
            ("date_of_birth", "Date of Birth", self.date_of_birth_input),
            ("age", "Age (months)", None),
            ("sex", "Sex", self.sex_combo),
            ("race", "Race", None),
            ("address", "Address", None),
            ("city", "City", None),
            ("state", "State", self.state_input),
            ("zip_code", "Zip Code", self.zip_code_input),
            ("home_phone", "Home Phone", self.home_phone_input),
            ("work_phone", "Work Phone", self.work_phone_input),
            ("best_time_to_call", "Best Time To Call", self.best_time_to_call_input),
            ("fax", "Fax", None),
            ("email", "Email", None),
            ("mother_name", "Mother Name", None),
            ("father_name", "Father Name", None),
            ("mother_age", "Mother Age", None),
            ("father_age", "Father Age", None),
            ("biological_mother", None, self.biological_mother_input),
            ("biological_mother_name", "Biological Mother Name", None),
            ("biological_father", None, self.biological_father_input),
            ("biological_father_name", "Biological Father Name", None),
            ("research_participation", None, self.research_participation_input),
            ("research_study", "Research Study", None),
            ("research_study_when", "When", None),
            ("research_study_where", "Where", None),
        ]

        form = QFormLayout()
        self.fields: dict[str, QWidget] = {}
        for key, label, widget in rows:
            if widget is None:
                # Plain text fields get a QLineEdit and the conventional
                # `<column>_input` attribute so they remain addressable.
                widget = QLineEdit()
                setattr(self, f"{key}_input", widget)
            if isinstance(widget, YesNoInput):
                widget.add_to_form(form)
            else:
                form.addRow(label, widget)
            self.fields[key] = widget

        save_button = QPushButton("Save Screening Questionnaire")
        save_button.setObjectName("PrimaryButton")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.save)

        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addStretch()
        scroll_area.setWidget(page)
        outer_layout.addWidget(scroll_area)

        self.load_existing_data()

    def load_existing_data(self) -> None:
        data = get_screening_questionnaire(self.patient_id)
        if not data:
            return

 
        for key, widget in self.fields.items():
            if isinstance(widget, YesNoInput):
                widget.set_value(data.get(key))
            else:
                widget.setText(data.get(key) or "")
        self.date_of_birth_input.setText(format_date(data.get("date_of_birth")))

    def collect_data(self) -> dict:
        return {
            key: widget.value() if isinstance(widget, YesNoInput) else widget.text().strip()
            for key, widget in self.fields.items()
        }

    def _validation_error(self) -> str | None:
        """Returns the first problem that would make the saved data unusable."""
        zip_code = self.zip_code_input.text().strip()
        # The validator stops bad typing, but legacy values loaded from the
        # database bypass it, so the lengths are checked again at save time.
        if zip_code and not (zip_code.isdigit() and len(zip_code) == ZIP_CODE_DIGITS):
            return f"Enter the zip code as {ZIP_CODE_DIGITS} digits."
        for label, phone in (("home", self.home_phone_input), ("work", self.work_phone_input)):
            if not phone.is_valid():
                return f"Enter the {label} phone number as {PhoneInput.NUMBER_DIGITS} digits."
        if not self.best_time_to_call_input.is_valid():
            return "Enter the best time to call as h:mm and choose AM or PM."
        return None

    def save(self, *, show_confirmation=True) -> bool:
        data = self.collect_data()
        error = self._validation_error()
        if error is None:
            try:
                data["date_of_birth"] = parse_date(data["date_of_birth"])
            except ValueError:
                error = f"Enter date of birth as {DATE_FORMAT}."
        if error:
            QMessageBox.warning(self, "Unable to save", error)
            return False
        save_screening_questionnaire(self.patient_id, data)
        if show_confirmation:
            QMessageBox.information(self, "Saved", "Screening questionnaire saved successfully.")
        return True
