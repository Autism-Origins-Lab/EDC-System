from pathlib import Path

import pandas as pd

from app.database.connection import get_connection

EXPORT_SHEETS = {
    "Patients": "patients",
    "Telephone Screening": "telephone_screenings",
    "Screening Questionnaire": "screening_questionnaires",
    "Medical History": "medical_histories",
    "Family Medical History": "family_medical_histories",
    "Procedure Schedule": "procedure_schedules",
    "Mullen Assessment": "mullen_assessments",
   # "Mullen Scores": "mullen_scores",
}


def export_patient_workbook(output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)