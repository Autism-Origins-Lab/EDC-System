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
}


def export_patient_workbook(output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, table_name in EXPORT_SHEETS.items():
                dataframe = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
                dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

        connection.execute(
            "INSERT INTO export_logs (output_path) VALUES (?)",
            (str(output_path),),
        )

    return output_path
