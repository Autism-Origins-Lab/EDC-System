import sqlite3

from app.database.connection import get_connection

PATIENT_FIELDS = {"subject_id", "child_name", "date_of_birth", "sex", "race", "form_status"}

#command to check database name: python -c "from app.database.connection import get_connection; m = get_connection(); c = m.__enter__(); print(dict(c.execute('PRAGMA database_list').fetchone())['file']); m.__exit__(None, None, None)"
def list_patients() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            #added another column called form_progress that helps mark formed as Pending or Complete.
            #a form is pending when a new patient is added to the database. a form is complete when it is marked complete and ready to export. 
            #FOR LATER: a patient's form is marked complete when they are ELIGIBLE and certain details are filled out. 
            #COALESCE returns the first non null value.
            """
            SELECT
                p.id,
                p.subject_id,
                COALESCE(p.child_name, '') AS child_name,
                COALESCE(ts.eligibility, 'Not started') AS eligibility,
                COALESCE(p.form_status, 'Pending') AS form_status,
                COALESCE(ts.screener, '') AS screener,
                COALESCE(ts.schedule_date, '') AS schedule_date
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
            ORDER BY p.created_at DESC, p.id DESC
            """
        ).fetchall()
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
            SELECT *
            FROM patients
            WHERE id = ?
            """,
            (patient_id,),
        ).fetchone()

    return dict(row) if row else None


def update_patient(patient_id: int, data: dict) -> None:
    fields = [key for key in data if key in PATIENT_FIELDS] # building a list of keys and extract corresponding values instead of relying on data.items() directly 
    #less risk of a mismatch.
    if not fields:
        return

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [data[field] for field in fields] + [patient_id]

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE patients
            SET {assignments},
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values,
        )


def search_patients(search_text: str) -> list[dict]:
    cleaned_search = search_text.strip().lower()

    if not cleaned_search:
        return list_patients()

    pattern = f"%{cleaned_search}%"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.subject_id,
                COALESCE(p.child_name, '') AS child_name,
                COALESCE(ts.eligibility, 'Not started') AS eligibility,
                COALESCE(p.form_status, 'Pending') AS form_status,
                COALESCE(ts.screener, '') AS screener,
                COALESCE(ts.schedule_date, '') AS schedule_date
                FROM patients p
                LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
                ORDER BY p.created_at DESC, p.id DESC
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
            WHERE
                LOWER(p.subject_id) LIKE ?
                OR LOWER(COALESCE(p.child_name, '')) LIKE ?
                OR LOWER(COALESCE(ts.eligibility, 'Not started')) LIKE ?
                OR LOWER(COALESCE(p.form_status, 'Pending')) LIKE ?
                OR LOWER(COALESCE(ts.screener, '')) LIKE ?
                OR LOWER(COALESCE(ts.schedule_date, '')) LIKE ?
            ORDER BY p.created_at DESC, p.id DESC
                
            """,
            (pattern, pattern, pattern, pattern, pattern, pattern),
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
            #for later, I want to make it so that you are only able to mark complete manually IF the patient is eligible.
            )
        if cursor.rowcount == 0:
            raise ValueError(f"There is no patient with id {patient_id}.")


def update_patient_eligibility(patient_id: int, status: str) -> None: #database method that marks form as complete --> ready export
  #primary column is id. Direct update w cursor.rowcount --> check existence better
  with get_connection() as connection:
        cursor = connection.execute(
                """
                UPDATE patients
                SET eligibility = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, patient_id),
            #for later, I want to make it so that you are only able to mark complete manually IF the patient is eligible.
            )
        if cursor.rowcount == 0:
            raise ValueError(f"There is no patient with id {patient_id}.")