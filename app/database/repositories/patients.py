import math
import sqlite3
from datetime import date, datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

from app.database.connection import get_connection

IDENTITY_FIELDS = {"child_name", "date_of_birth", "sex", "race"}
PATIENT_FIELDS = {"subject_id", *IDENTITY_FIELDS, "form_status", "risk"}

AGE_CUTOFF = 3  # months; a born baby must be younger than this
GESTATIONAL_AGE_CUTOFF = 37  # weeks; born at or before this is ineligible

AGE_REASON = f"Age is {AGE_CUTOFF} months or older."
GESTATION_REASON = f"Born at or before {GESTATIONAL_AGE_CUTOFF} weeks gestation."
AUTOMATIC_REASONS = {AGE_REASON, GESTATION_REASON, f"{AGE_REASON} {GESTATION_REASON}"}

FILTER_YES = "Yes Only"
FILTER_NO = "No Only"
FILTER_NOT_EVALUATED = "Not Evaluated Only"

FILTER_HIGH_RISK = "High Risk Only"
FILTER_LOW_RISK = "Low Risk Only"
FILTER_NOT_EVALUATED_RISK = "Risk Not Evaluated Only"

ELIGIBILITY_FILTERS = {
    "Yes Only": "LOWER(TRIM(COALESCE(eligibility, ''))) = 'yes'",
    "No Only": "LOWER(TRIM(COALESCE(eligibility, ''))) = 'no'",
    "Not Evaluated Only": "LOWER(TRIM(COALESCE(eligibility, ''))) = 'not evaluated'",
}

RISK_FILTERS = {
    "High Risk Only": "risk = 1", #true
    "Low Risk Only": "risk = 0", #false
    "Risk Not Evaluated Only": "risk IS NULL",
}

SORT_OPTIONS = {
    "Name (A-Z)": "COALESCE(child_name, subject_id) COLLATE NOCASE ASC",
    "Name (Z-A)": "COALESCE(child_name, subject_id) COLLATE NOCASE DESC",
    "Schedule Date (Earliest First)": "schedule_date IS NULL, schedule_date ASC",
    "Schedule Date (Latest First)": "schedule_date IS NULL, schedule_date DESC",
    "Newest First": "created_at DESC, id DESC",
}

def _to_number(value) -> float | None:
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    return None if math.isnan(number) else number


def _to_date(value) -> date | None:
    for date_format in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except (ValueError, TypeError, AttributeError):
            continue
    return None


def ineligibility_reason(
    age: str | None,
    gest_age: str | None,
    date_of_birth: str | None,
    today: date | None = None,
) -> str | None:
    """Return why a patient is ineligible, or None if no rule is violated.

    Both rules are checked once the baby is born. Age is measured from the date of
    birth to today; the typed-in age (months) is the fallback when no date of birth is entered.
    """
    today = today or date.today()
    birthday = _to_date(date_of_birth)
    months = _to_number(age)

    if birthday is not None:
        if birthday > today:
            return None  # not born yet
        too_old = today >= birthday + relativedelta(months=AGE_CUTOFF)
    elif months is not None:
        too_old = months >= AGE_CUTOFF
    else:
        return None  # no evidence the baby has been born

    reasons = []
    if too_old:
        reasons.append(AGE_REASON)
    weeks = _to_number(gest_age)
    if weeks is not None and weeks <= GESTATIONAL_AGE_CUTOFF:
        reasons.append(GESTATION_REASON)
    return " ".join(reasons) or None


def apply_automatic_eligibility(connection: sqlite3.Connection, patient_id: int) -> None:
    """Mark the patient ineligible with the reason as the comment when a rule is violated.

    If a rule no longer applies -> "No" goes back to "Not evaluated". Custom eligibility comment takes priority
    """
    row = connection.execute(
        """
        SELECT p.date_of_birth, sq.age, ts.gestational, ts.eligibility, ts.eligibility_comment
        FROM patients p
        LEFT JOIN screening_questionnaires sq ON sq.patient_id = p.id
        LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
        WHERE p.id = ?
        """,
        (patient_id,),
    ).fetchone()
    if row is None:
        return
    comment = (row["eligibility_comment"] or "").strip()
    if row["eligibility"] == "No" and comment and comment not in AUTOMATIC_REASONS:
        return
    reason = ineligibility_reason(row["age"], row["gestational"], row["date_of_birth"])
    if reason is None:
        if row["eligibility"] == "No" and comment in AUTOMATIC_REASONS:
            connection.execute(
                """
                UPDATE telephone_screenings
                SET eligibility = 'Not evaluated',
                    eligibility_comment = '',
                    updated_at = CURRENT_TIMESTAMP
                WHERE patient_id = ?
                """,
                (patient_id,),
            )
        return
    connection.execute(
        """
        INSERT INTO telephone_screenings (patient_id, eligibility, eligibility_comment)
        VALUES (?, 'No', ?)
        ON CONFLICT(patient_id) DO UPDATE SET
            eligibility = excluded.eligibility,
            eligibility_comment = excluded.eligibility_comment,
            updated_at = CURRENT_TIMESTAMP
        """,
        (patient_id, reason),
    )


def list_patients(sort_by: str = "Newest First", eligibility_filter: str | None = None, risk_filter: str | None = None) -> list[dict]:
    order_by = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["Newest First"])

    conditions = []
    if eligibility_filter:
        conditions.append(ELIGIBILITY_FILTERS[eligibility_filter])
    if risk_filter:
        conditions.append(RISK_FILTERS[risk_filter])
    query = """
        SELECT * FROM (
            SELECT
                p.id,
                p.subject_id,
                p.child_name,
                p.form_status,
                p.created_at,
                COALESCE(NULLIF(TRIM(ts.eligibility), ''), 'Not evaluated') AS eligibility,
                p.risk AS risk, 
                ts.screener,
                ts.schedule_date,
                ts.eligibility_comment AS comment
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
        )
    """
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
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
                COALESCE(NULLIF(TRIM(ts.eligibility), ''), 'Not evaluated') AS eligibility
            FROM patients p
            LEFT JOIN telephone_screenings ts ON ts.patient_id = p.id
            WHERE p.id = ?
            """,
            (patient_id,),
        ).fetchone()

    return dict(row) if row else None


def delete_patient(patient_id: int) -> None:
    """Delete a patient and all dependent records via foreign-key cascades."""
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        if not cursor.rowcount:
            raise ValueError("Patient does not exist.")


def update_patient(patient_id: int, data: dict) -> None:
    with get_connection() as connection:
        _update_patient(connection, patient_id, data)
        # The Overview tab saves the date of birth here, so re-check eligibility.
        if "date_of_birth" in data:
            apply_automatic_eligibility(connection, patient_id)


def _update_patient(connection: sqlite3.Connection, patient_id: int, data: dict) -> None:
    """Update shared fields and their legacy form copies in the same transaction."""
    fields = {key: value for key, value in data.items() if key in PATIENT_FIELDS}
    if not fields:
        return
    if "subject_id" in fields:
        fields["subject_id"] = fields["subject_id"].strip()
        if not fields["subject_id"]:
            raise ValueError("Subject ID is required.")
    if "risk" in fields and fields["risk"] not in (None, 0, 1):
        raise ValueError("Familial risk must be high, low, or not selected.")
    assignments = ", ".join(f"{field} = ?" for field in fields)
    try:
        cursor = connection.execute(
            f"UPDATE patients SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            [*fields.values(), patient_id],
        )
    except sqlite3.IntegrityError as exc:
        if "subject_id" in str(exc):
            raise ValueError("A patient with this subject ID already exists.") from exc
        raise
    if not cursor.rowcount:
        raise ValueError("Patient does not exist.")
    identity = {key: value for key, value in fields.items() if key in IDENTITY_FIELDS}
    if identity:
        assignments = ", ".join(f"{field} = ?" for field in identity)
        connection.execute(
            f"UPDATE screening_questionnaires SET {assignments}, updated_at = CURRENT_TIMESTAMP "
            "WHERE patient_id = ?",
            [*identity.values(), patient_id],
        )
    if "risk" in fields:
        risk = fields["risk"]
        connection.execute("""
            INSERT INTO telephone_screenings (patient_id, high_familial_risk, low_familial_risk)
            VALUES (?, ?, ?)
            ON CONFLICT(patient_id) DO UPDATE SET
                high_familial_risk = excluded.high_familial_risk,
                low_familial_risk = excluded.low_familial_risk,
                updated_at = CURRENT_TIMESTAMP
        """, (patient_id, int(risk == 1), int(risk == 0)))


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
                COALESCE(ts.eligibility, 'Not evaluated') AS eligibility,
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
                OR LOWER(COALESCE(NULLIF(TRIM(ts.eligibility), ''), 'Not evaluated')) LIKE ?
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
                 WHERE patient_id = ?
                 """,
                (eligibility_status, patient_id),
            )
        else:
            connection.execute(
                        """
                        INSERT INTO telephone_screenings (patient_id, eligibility)
                        VALUES (?, ?)
                        """,
                       (patient_id, eligibility_status),
                    )
        connection.commit()    

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
