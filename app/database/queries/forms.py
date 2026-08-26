from app.database.connection import get_connection

FORM_FIELDS = {
    "telephone_screenings": {
        "screening_date",
        "appointment_date",
        "screener",
        "eligibility",
        "high_familial_risk",
        "low_familial_risk",
        "schedule_date",
        "birthweight",
        "gestational",
        "verbal_consent",
        "consent_initials",
    },
    "screening_questionnaires": {
        "parent_name",
        "child_name",
        "date_of_birth",
        "age",
        "sex",
        "race",
        "address",
        "city",
        "state",
        "zip_code",
        "home_phone",
        "work_phone",
        "best_time_to_call",
        "fax",
        "email",
        "mother_name",
        "father_name",
        "mother_age",
        "father_age",
        "biological_mother",
        "biological_mother_name",
        "biological_father",
        "biological_father_name",
        "research_participation",
        "research_study",
        "research_study_when",
        "research_study_where",
    },
    "medical_histories": {
        "general_health",
        "seen_neurologist",
        "neurologist_description",
        "head_injury",
        "head_injury_description",
        "genetic_abnormalities",
        "genetic_abnormalities_description",
        "seizure_epileptic_attack",
        "gestational_age",
        "birthweight",
        "birthlength",
        "pregnancy_complications",
        "pregnancy_complications_description",
    },
    "family_medical_histories": {
        "family_psychiatric",
        "family_psychiatric_description",
        "parent_autism",
        "parent_schizophrenia",
        "parent_learning_disability",
        "parent_substance_abuse",
        "has_siblings",
        "sibling_autism",
        "sibling_adhd",
        "same_father_as_older_sibling",
        "same_mother_as_older_sibling",
    },
}


def _filter_fields(table_name: str, data: dict) -> dict:
    allowed_fields = FORM_FIELDS[table_name]
    return {key: value for key, value in data.items() if key in allowed_fields}


def _save_one_to_one_form(table_name: str, patient_id: int, data: dict) -> None:
    fields = _filter_fields(table_name, data)

    columns = ["patient_id", *fields.keys()]
    placeholders = ", ".join("?" for _ in columns)

    update_assignments = [
        f"{field} = excluded.{field}"
        for field in fields
    ]
    update_assignments.append("updated_at = CURRENT_TIMESTAMP")

    sql = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(patient_id)
        DO UPDATE SET {", ".join(update_assignments)}
    """

    with get_connection() as connection:
        connection.execute(sql, [patient_id, *fields.values()])


def _get_one_to_one_form(table_name: str, patient_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM {table_name} WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()

    return dict(row) if row else None


def save_telephone_screening(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("telephone_screenings", patient_id, data)


def get_telephone_screening(patient_id: int) -> dict | None:
    return _get_one_to_one_form("telephone_screenings", patient_id)


def save_screening_questionnaire(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("screening_questionnaires", patient_id, data)


def get_screening_questionnaire(patient_id: int) -> dict | None:
    return _get_one_to_one_form("screening_questionnaires", patient_id)


def save_medical_history(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("medical_histories", patient_id, data)


def get_medical_history(patient_id: int) -> dict | None:
    return _get_one_to_one_form("medical_histories", patient_id)


def save_family_medical_history(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("family_medical_histories", patient_id, data)


def get_family_medical_history(patient_id: int) -> dict | None:
    return _get_one_to_one_form("family_medical_histories", patient_id)


def save_procedure_schedule(patient_id: int,procedure_name: str,data: dict) -> None:
    procedure_name = procedure_name.strip()
    if not procedure_name:
        raise ValueError("Procedure name is required.")

    fields = {
        key: value
        for key, value in data.items()
        if key in {"procedure_time", "research_assistant", "room"}
    }

    columns = ["patient_id", "procedure_name", *fields.keys()]
    placeholders = ", ".join("?" for _ in columns)

    update_assignments = [
        f"{field} = excluded.{field}"
        for field in fields
    ]
    update_assignments.append("updated_at = CURRENT_TIMESTAMP")

    sql = f"""
        INSERT INTO procedure_schedules ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(patient_id, procedure_name)
        DO UPDATE SET {", ".join(update_assignments)}
    """

    with get_connection() as connection:
        connection.execute(
            sql,
            [patient_id, procedure_name, *fields.values()],
        )

def list_procedure_schedules(patient_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM procedure_schedules
            WHERE patient_id = ?
            ORDER BY procedure_name
            """,
            (patient_id,),
        ).fetchall()

    return [dict(row) for row in rows]

PENDING_FORM_TABLES = {
    "Telephone Screening": ("telephone_screenings", "Telephone Screening"),
    "Screening Questionnaire": ("screening_questionnaires", "Screening Questionnaire"),
    "Medical History": ("medical_histories", "Medical History"),
    "Family Medical History": ("family_medical_histories", "Family Medical History"),
}

PROCEDURE_NAMES = ("Consents", "Recording", "Neuropsych")


def list_pending_forms(form_name: str | None = None) -> list[dict]:
    rows = []

    selected_forms = (
        {form_name: PENDING_FORM_TABLES[form_name]}
        if form_name in PENDING_FORM_TABLES
        else PENDING_FORM_TABLES
    )

    with get_connection() as connection:
        for label, (table_name, tab_name) in selected_forms.items():
            pending = connection.execute(
                f"""
                SELECT
                    p.id AS patient_id,
                    p.subject_id,
                    COALESCE(p.child_name, '') AS child_name,
                    ? AS form_name,
                    ? AS tab_name,
                    '' AS detail
                FROM patients p
                WHERE NOT EXISTS (
                    SELECT 1 FROM {table_name} f WHERE f.patient_id = p.id
                )
                ORDER BY p.created_at DESC, p.id DESC
                """,
                (label, tab_name),
            ).fetchall()
            rows.extend(dict(row) for row in pending)

        if form_name in (None, "Procedure Schedule"):
            for procedure_name in PROCEDURE_NAMES:
                pending = connection.execute(
                    """
                    SELECT
                        p.id AS patient_id,
                        p.subject_id,
                        COALESCE(p.child_name, '') AS child_name,
                        'Procedure Schedule' AS form_name,
                        'Procedure Schedule' AS tab_name,
                        ? AS detail
                    FROM patients p
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM procedure_schedules ps
                        WHERE ps.patient_id = p.id
                          AND ps.procedure_name = ?
                    )
                    ORDER BY p.created_at DESC, p.id DESC
                    """,
                    (procedure_name, procedure_name),
                ).fetchall()
                rows.extend(dict(row) for row in pending)

    return rows