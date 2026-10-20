from pathlib import Path
from tempfile import NamedTemporaryFile

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
    "Mullen Scores": "mullen_scores",
}


def export_patient_workbook(output_path: Path) -> Path:
    """Export stored records, preserving the destination if workbook creation fails."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Close the temporary file before openpyxl opens it, including on Windows.
    with NamedTemporaryFile(
        dir=output_path.parent,
        prefix=".edc-export-",
        suffix=output_path.suffix,
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with get_connection() as connection:
            with pd.ExcelWriter(temporary_path, engine="openpyxl") as writer:
                for sheet_name, table_name in EXPORT_SHEETS.items():
                    dataframe = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
                    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

            connection.execute(
                "INSERT INTO export_logs (output_path) VALUES (?)",
                (str(output_path),),
            )
            temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return output_path
