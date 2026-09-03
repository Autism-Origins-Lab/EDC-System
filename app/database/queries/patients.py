import sqlite3

from app.database.connection import get_connection

PATIENT_FIELDS = {"subject_id", "child_name", "date_of_birth", "sex", "race"}


def list_patients() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.subject_id,
                COALESCE(p.child_name, '') AS child_name,
                COALESCE(ts.eligibility, 'Not started', 'Eligible') AS eligibility,
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
    fields = {
        key: value
        for key, value in data.items()
        if key in PATIENT_FIELDS
    }

    if not fields:
        return

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [*fields.values(), patient_id]

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
                COALESCE(ts.screener, '') AS screener,
                COALESCE(ts.schedule_date, '') AS schedule_date
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
            WHERE lower(p.subject_id) LIKE ?
               OR lower(COALESCE(p.child_name, '')) LIKE ?
               OR lower(COALESCE(p.date_of_birth, '')) LIKE ?
               OR lower(COALESCE(p.sex, '')) LIKE ?
               OR lower(COALESCE(p.race, '')) LIKE ?
            ORDER BY p.created_at DESC, p.id DESC
            """,
            (pattern, pattern, pattern, pattern, pattern),
        ).fetchall()

    return [dict(row) for row in rows]

def update_patient_eligibility(patient_id: int, status: str) -> None: #database method that marks eligibility as eligible --> ready export
  with get_connection() as connection:
        cursor = connection.execute(
            "SELECT 1 FROM telephone_screenings WHERE patient_id = ?",
            (patient_id,)
        )
        if cursor.fetchone():
            connection.execute(
                """
                UPDATE telephone_screenings
                SET eligibility = ?
                WHERE patient_id = ?
                """,
                (status, patient_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO telephone_screenings (patient_id, eligibility)
                VALUES (?, ?)
                """,
                (patient_id, status),
            )
