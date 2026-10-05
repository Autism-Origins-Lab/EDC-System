import pandas as pd
import sqlite3

from app.database.connection import get_connection

PATIENT_FIELDS = {"subject_id", "child_name", "date_of_birth", "sex", "race", "form_status"}

FILTER_YES = "Yes Only"
FILTER_NO = "No Only"
FILTER_NOT_EVALUATED = "Not Evaluated Only"

FILTER_HIGH_RISK = "High Risk Only"
FILTER_LOW_RISK = "Low Risk Only"

ELIGIBILITY_FILTERS = {
    "Yes Only": "LOWER(TRIM(COALESCE(eligibility, ''))) = 'yes'",
    "No Only": "LOWER(TRIM(COALESCE(eligibility, ''))) = 'no'",
    "Not Evaluated Only": "LOWER(TRIM(COALESCE(ts.eligibility, ''))) IN ('not evaluated', '') OR ts.eligibility IS NULL",
}

#deal with this later

RISK_FILTERS = {
    #might be better to change telephone screenings to boolean 
    "High Only": "LOWER(TRIM(COALESCE(high_familial_risk, ''))) = 'True'",
    "Low Only": "LOWER(TRIM(COALESCE(low_familial_risk, ''))) = 'True'",
}
#ignore for now

SORT_OPTIONS = {
    "Name (A-Z)": "COALESCE(child_name, subject_id) COLLATE NOCASE ASC",
    "Name (Z-A)": "COALESCE(child_name, subject_id) COLLATE NOCASE DESC",
    "Schedule Date (Earliest First)": "schedule_date IS NULL, schedule_date ASC",
    "Schedule Date (Latest First)": "schedule_date IS NULL, schedule_date DESC",
    "Newest First": "created_at DESC, id DESC",
}


def list_patients(sort_by: str = "Newest First", eligibility_filter: str | None = None,) -> list[dict]:
    order_by = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["Newest First"])
    where = ELIGIBILITY_FILTERS.get(eligibility_filter)

    where = None
    if eligibility_filter is not None:
        where = ELIGIBILITY_FILTERS[eligibility_filter]

    query = """
        SELECT * FROM (
            SELECT
                p.id,
                p.subject_id,
                p.child_name,
                p.form_status,
                p.created_at,
                ts.eligibility,
                ts.screener,
                ts.schedule_date,
                ts.eligibility_comment AS comment
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
        )
    """
    if where:
        query += f" WHERE {where}"
    query += f" ORDER BY {order_by}"

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def create_patient(subject_id: str) -> int:
    cleaned_subject_id = subject_id.strip()
    if not cleaned_subject_id:
        raise ValueError("Subject ID is required.")

    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO patients (subject_id) VALUES (?)",
                (cleaned_subject_id,),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("A patient with this subject ID already exists.") from exc

        return int(cursor.lastrowid)


def get_patient(patient_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 
                p.*,
                COALESCE(ts.eligibility, 'Not Evaluated') AS eligibility
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
            WHERE p.id = ?
            """,
            (patient_id,),
        ).fetchone()

    return dict(row) if row else None


def update_patient(patient_id: int, data: dict) -> None:
    fields = [key for key in data if key in PATIENT_FIELDS]
    if not fields:
        return

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [data[field] for field in fields] + [patient_id]

    with sqlite3.connect("data/patient_data.db") as connection:
        connection.execute(
            f"""
            UPDATE patients
            SET {assignments},
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values,
        )
    connection.commit()   


def search_patients(search_text: str, sort_by: str = "Newest First") -> list[dict]:
    cleaned_search = search_text.strip().lower()

    if not cleaned_search:
        return list_patients(sort_by=sort_by)

    pattern = f"%{cleaned_search}%"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.subject_id,
                COALESCE(p.child_name, '') AS child_name,
                COALESCE(ts.eligibility, 'Not started') AS eligibility,
                COALESCE(ts.eligibility_comment, '') AS comment,
                COALESCE(p.form_status, 'Pending') AS form_status,
                COALESCE(ts.screener, '') AS screener,
                COALESCE(ts.schedule_date, '') AS schedule_date
            FROM patients p
            LEFT JOIN telephone_screenings ts
                ON ts.patient_id = p.id
            WHERE
                LOWER(p.subject_id) LIKE ?
                OR LOWER(COALESCE(p.child_name, '')) LIKE ?
                OR LOWER(COALESCE(ts.eligibility, 'Not started')) LIKE ?
                OR LOWER(COALESCE(p.form_status, 'Pending')) LIKE ?
                OR LOWER(COALESCE(ts.screener, '')) LIKE ?
                OR LOWER(COALESCE(ts.schedule_date, '')) LIKE ?
                OR LOWER(COALESCE(ts.eligibility_comment, '')) LIKE ?
            ORDER BY p.created_at DESC, p.id DESC
            """,
            (pattern, pattern, pattern, pattern, pattern, pattern, pattern),
        ).fetchall()

    return [dict(row) for row in rows]

def update_patient_form(patient_id: int, status: str) -> None: #database method that marks form as complete --> ready export
  #primary column is id. Direct update w cursor.rowcount --> check existence better
  with get_connection() as connection:
        cursor = connection.execute(
                """
                UPDATE patients
                SET form_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, patient_id),
            )
        connection.commit()        
        if cursor.rowcount == 0:
            raise ValueError(f"There is no patient with id {patient_id}.")


#screening questionaire -> months (if >= 3 months, mark ineligible.)
#gestational age (telephone screening) -> weeks (if <37 automatically mark ineligible.)
#default value for eligibility should be not evaluated, not N/A

def update_patient_eligibility(patient_id: int, eligibility_status: str) -> None: #can't mark eligible on certain conditions TBA
  with get_connection() as connection:
        cursor = connection.execute(
                "SELECT 1 FROM telephone_screenings WHERE patient_id = ?",
                (patient_id,)
            )
        screening_exists = cursor.fetchone()
        if screening_exists: # update the eligibility status already in the screening, so that it doesn't crash & prevents a no column eligibility error
            connection.execute(
                 """
                 UPDATE telephone_screenings
                 SET eligibility = ?,
                    updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?
                 """,
                (eligibility_status, patient_id),
            )
        else:
            connection.execute( # if there is no record found, create one and set an eligibility. 
                        """
                        INSERT INTO telephone_screenings (patient_id, eligibility)
                        VALUES (?, ?)
                        """,
                       (patient_id, eligibility_status),
                    )
        connection.commit()    
        if cursor.rowcount == 0:
            raise ValueError(f"There is no patient with id {patient_id}.")

def export_patients_to_csv(file_path: str, patients: list[dict] | None = None) -> None:
    patients_to_export = patients if patients is not None else list_patients()
    dataframe = pd.DataFrame(patients_to_export)
    dataframe.to_csv(
        file_path,
        index=False,
        columns=[
            "subject_id",
            "child_name",
            "eligibility",
            "comment",
            "form_status",
            "screener",
            "schedule_date",
        ],
    )
    