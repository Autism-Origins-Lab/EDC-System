from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
import io
import urllib.request

from app.database.queries.patients import get_patient
from app.database.queries.forms import (
    get_telephone_screening,
    get_screening_questionnaire,
    get_medical_history,
    get_family_medical_history,
    list_procedure_schedules,
)


LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "migration.png"

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
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),   # full grid instead of LINEBELOW
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table

def _section_box(title: str, rows: list[list[tuple[str, str]]]) -> Table:
    data = [[title, "", ""]]
    for row in rows:
        # flatten each (label, value) pair into "Label: Value" per cell
        cells = [f"{label}{value}" for label, value in row]
        while len(cells) < 3:
            cells.append("")  # pad if a row has fewer than 3 items
        data.append(cells)

    table = Table(data, colWidths=[165, 165, 165])
    table.setStyle(TableStyle([
        # header row
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # body rows
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#555555")),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        # box only, no inner grid lines
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table

def _title_box(title: str, subtitle: str = "", width: int = 495) -> Table:
    style = styles["Normal"].clone("TitleBoxStyle")
    style.fontName = "Helvetica-Bold"
    style.fontSize = 16
    style.alignment = TA_CENTER
    style.leading = 20  # line spacing between the two lines

    text = title
    if subtitle:
        text += f"<br/><font size=11 name='Helvetica'>{subtitle}</font>"

    para = Paragraph(text, style)

    table = Table([[para]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef1f5")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return table

def _section_box_2col(title: str, rows: list[tuple[str, str]], width: int = 468) -> Table:
    label_width = 180
    value_width = width - label_width

    # wrap both label and value in Paragraphs so long text actually wraps
    # instead of overflowing into the next column
    label_style = styles["Normal"].clone("Label")
    label_style.fontName = "Helvetica-Bold"
    label_style.textColor = colors.HexColor("#555555")
    label_style.fontSize = 10

    value_style = styles["Normal"].clone("Value")
    value_style.fontSize = 10

    data = [[title, ""]]
    for label, value in rows:
        data.append([
            Paragraph(label, label_style),
            Paragraph(value, value_style),
        ])

    table = Table(data, colWidths=[label_width, value_width])
    table.setStyle(TableStyle([
        # header row (title spans both columns)
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),

        # body rows
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),      # bold labels in left column
        ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#555555")),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),

        # outer box, no inner grid lines (per your earlier preference)
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#999999")),
        ("LINEAFTER", (0,1), (0,-1), 0.5, colors.HexColor("#cccccc")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table

def _logo(width: int = 70) -> Image | None:              # NEW
    if not LOGO_PATH.exists():
        return None
    iw, ih = ImageReader(str(LOGO_PATH)).getSize()
    img = Image(str(LOGO_PATH), width=width, height=width * ih / iw, mask="auto")
    img.hAlign = "LEFT"
    return img

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

    logo = _logo()                                       # NEW: call the helper
    if logo:
        story.append(logo)
        story.append(Spacer(1, 8))

    story.append(Paragraph(f"Patient Report", styles["Title"]))
    story.append(Spacer(1, 16))


    story.append(_section_box("Patient Info", [
        [("Name: ", _text(questionnaire.get("child_name"))),
        ("ID: ", _text(patient["subject_id"])),
        ("DOB: ", _text(questionnaire.get("date_of_birth")))],
        [("Age: ", _text(questionnaire.get("age"))),
         ("Sex: ", _text(questionnaire.get("sex"))),
         ("Screener: ", _text(screening.get("screener")))],
        [("Eligibility: ", _text(screening.get("eligibility"))),
        ("Schedule Date: ", _text(screening.get("schedule_date"))),
        ("Race: ", _text(questionnaire.get("race")))],
    ]))
    story.append(Spacer(1, 12))

    story.append(_title_box("Department of Psychology - AOL", f"Queens College"))
    story.append(Spacer(1, 12))
    """
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
    """
    story.append(_section_box_2col("Medical History", [
        ("General Health", _text(medical.get("general_health"))),
        ("Seen neurologist", _yes_no(medical.get("seen_neurologist"))),
        ("Head injury", _yes_no(medical.get("head_injury"))),
        ("Head injury details", _text(medical.get("head_injury_description"))),
        ("Genetic abnormalities Such as Fragile X or Down?", _yes_no(medical.get("genetic_abnormalities"))),
        ("Seizure/epileptic attack", _yes_no(medical.get("seizure_epileptic_attack"))),
        ("Gestational Age(weeks)", _text(medical.get("gestational_age"))),
        ("Birthweight(pounds/ounces or kilograms/grams)", _text(medical.get("birthweight"))),
        ("Birthlength(inches or centimeters)", _text(medical.get("birthlength"))),
        ("Pregnancy Complication", _yes_no(medical.get("pregnancy_complications"))),
        ("Pregnancy Complication details", _text(medical.get("pregnancy_complications_description"))),
    ]))


    story.append(Spacer(1, 12))


    """
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
    """
    story.append(Spacer(1, 12))
    story.append(_section_box_2col("Family Medical History",[
        ("Family Psychiatric Illness", _yes_no(family.get("family_psychiatric"))),
        ("Family Psychiatric Illness Description", _text(family.get("family_psychiatric_description"))),
        ("Either mother or father been diagnosed with Autism", _yes_no(family.get("parent_autism"))),
        ("Either mother or father been diagnosed with Schizophrenia", _yes_no(family.get("parent_schizophrenia"))),
        ("Either mother or father been diagnosed with a learning or intellectual disability", _yes_no(family.get("parent_learning_disability"))),
        ("Either mother or father has a history of substance abuse", _yes_no(family.get("parent_substance_abuse"))),
        ("Does the child have any siblings", _yes_no(family.get("has_siblings"))),
        ("Siblings with Autism", _yes_no(family.get("sibling_autism"))),
        ("Siblings with ADHD", _yes_no(family.get("sibling_adhd"))),
       ]))
    """
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
    """
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