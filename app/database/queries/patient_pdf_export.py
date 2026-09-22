from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from app.database.queries.patients import get_patient
from app.database.queries.forms import (
    get_telephone_screening,
    get_screening_questionnaire,
    get_medical_history,
    get_family_medical_history,
    list_procedure_schedules,
)


def _yes_no(value) -> str:
    if value is None:
        return "No data"
    return "Yes" if value else "No"


def _text(value) -> str:
    return value if value else "No data"


def _section_table(rows: list[tuple[str, str]]) -> Table:
    table = Table(rows, colWidths=[180, 320])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e0e0e0")),
    ]))
    return table


def build_patient_pdf(patient_id: int, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    patient = get_patient(patient_id)
    if not patient:
        raise ValueError(f"No patient found with id {patient_id}")

    questionnaire = get_screening_questionnaire(patient_id) or {}
    screening = get_telephone_screening(patient_id) or {}
    medical = get_medical_history(patient_id) or {}
    family = get_family_medical_history(patient_id) or {}
    procedures = list_procedure_schedules(patient_id)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Patient report — {patient['subject_id']}", styles["Title"]))
    story.append(Paragraph(
        f"{_text(patient.get('child_name'))} &nbsp;&nbsp; DOB: {_text(patient.get('date_of_birth'))}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Demographics", styles["Heading2"]))
    story.append(_section_table([
        ("Sex", _text(questionnaire.get("sex"))),
        ("Race", _text(questionnaire.get("race"))),
        ("City", _text(questionnaire.get("city"))),
        ("State", _text(questionnaire.get("state"))),
    ]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Telephone screening", styles["Heading2"]))
    story.append(_section_table([
        ("Eligibility", _text(screening.get("eligibility"))),
        ("High familial risk", _yes_no(screening.get("high_familial_risk"))),
        ("Low familial risk", _yes_no(screening.get("low_familial_risk"))),
        ("Screener", _text(screening.get("screener"))),
        ("Schedule date", _text(screening.get("schedule_date"))),
    ]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Medical history", styles["Heading2"]))
    story.append(_section_table([
        ("General health", _text(medical.get("general_health"))),
        ("Seen neurologist", _yes_no(medical.get("seen_neurologist"))),
        ("Head injury", _yes_no(medical.get("head_injury"))),
        ("Head injury details", _text(medical.get("head_injury_description"))),
        ("Genetic abnormalities", _yes_no(medical.get("genetic_abnormalities"))),
        ("Seizure/epileptic attack", _yes_no(medical.get("seizure_epileptic_attack"))),
        ("Gestational age", _text(medical.get("gestational_age"))),
        ("Birthweight", _text(medical.get("birthweight"))),
        ("Birthlength", _text(medical.get("birthlength"))),
        ("Pregnancy complications", _yes_no(medical.get("pregnancy_complications"))),
    ]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Family medical history", styles["Heading2"]))
    story.append(_section_table([
        ("Family psychiatric illness", _yes_no(family.get("family_psychiatric"))),
        ("Parent — autism", _yes_no(family.get("parent_autism"))),
        ("Parent — schizophrenia", _yes_no(family.get("parent_schizophrenia"))),
        ("Parent — learning disability", _yes_no(family.get("parent_learning_disability"))),
        ("Parent — substance abuse", _yes_no(family.get("parent_substance_abuse"))),
        ("Has siblings", _yes_no(family.get("has_siblings"))),
        ("Sibling — autism", _yes_no(family.get("sibling_autism"))),
        ("Sibling — ADHD", _yes_no(family.get("sibling_adhd"))),
    ]))
    story.append(Spacer(1, 12))

    if procedures:
        story.append(Paragraph("Procedure schedule", styles["Heading2"]))
        rows = [("Procedure", "Time", "Room", "Research assistant")]
        for proc in procedures:
            rows.append((
                proc.get("procedure_name", ""),
                proc.get("procedure_time", "") or "—",
                proc.get("room", "") or "—",
                proc.get("research_assistant", "") or "—",
            ))
        proc_table = Table(rows, colWidths=[130, 90, 90, 160])
        proc_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ]))
        story.append(proc_table)

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    doc.build(story)

    return output_path