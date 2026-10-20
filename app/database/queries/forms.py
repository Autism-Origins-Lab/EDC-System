from app.database.connection import get_connection

MULLEN_DOMAINS=(
    "gross_motor",
    "visual_reception",
    "fine_motor",
    "receptive_language",
    "expressive_language",
)

MULLEN_SCORE_FIELDS=(
    "raw_score",
    "t_score",
    "band_of_error",
    "percentile_rank",
    "descriptive_category",
    "age_equivalence",
)

MULLEN_FIELDS= {
    f"{domain}_{field}"
    for domain in MULLEN_DOMAINS
    for field in MULLEN_SCORE_FIELDS
}

FORM_FIELDS = {
    "telephone_screenings": {
        "screening_date",
        "appointment_date",
        "screener",
        "eligibility",
        "eligibility_comment",
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
        "sibling_autism_full",
        "sibling_autism_half",
        "sibling_autism_adopted",
        "sibling_autism_multiple",
        "sibling_adhd_full",
        "sibling_adhd_half",
        "sibling_adhd_adopted",
        "sibling_adhd_multiple",
    },
    "mullen_assessments": MULLEN_FIELDS,
}


def _filter_fields(table_name: str, data: dict) -> dict:
    allowed_fields = FORM_FIELDS[table_name]
    return {key: value for key, value in data.items() if key in allowed_fields}

# Universal Save Function --> Database
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
        if table_name == "telephone_screenings":
            
            # Read the saved row so partial form updates preserve existing risk.
            screening = connection.execute(
                "SELECT high_familial_risk, low_familial_risk "
                "FROM telephone_screenings WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
            
            high = bool(screening["high_familial_risk"])
            low = bool(screening["low_familial_risk"])
            
            if high and low:
                raise ValueError("Select either high or low familial risk, not both.")
            risk = True if high else False if low else None
            
            # Commit the screening and patient risk together.
            connection.execute(
                "UPDATE patients SET risk = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (risk, patient_id),
            )


def _get_one_to_one_form(table_name: str, patient_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM {table_name} WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()

    return dict(row) if row else None

# Mullen Assessment
def save_mullen_assessment(patient_id: int, data: dict) -> None:
    invalid_domains = set(data) - set(MULLEN_DOMAINS)
    if invalid_domains:
        invalid = ", ".join(sorted(invalid_domains))
        raise ValueError(f"Unknown Mullen domain(s): {invalid}")

    with get_connection() as connection:
        assessment = connection.execute(
            """
            SELECT id
            FROM mullen_assessments
            WHERE patient_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (patient_id,),
        ).fetchone()

        if assessment:
            assessment_id = assessment["id"]
            connection.execute(
                """
                UPDATE mullen_assessments
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (assessment_id,),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO mullen_assessments (patient_id)
                VALUES (?)
                """,
                (patient_id,),
            )
            assessment_id = cursor.lastrowid

        for domain in MULLEN_DOMAINS:
            if domain not in data:
                continue

            score_data = data[domain]
            if not isinstance(score_data, dict):
                raise TypeError(f"Scores for {domain} must be a dictionary.")

            invalid_fields = set(score_data) - set(MULLEN_SCORE_FIELDS)
            if invalid_fields:
                invalid = ", ".join(sorted(invalid_fields))
                raise ValueError(f"Unknown score field(s) for {domain}: {invalid}")

            values = [score_data.get(field) for field in MULLEN_SCORE_FIELDS]
            existing_score = connection.execute(
                """
                SELECT id
                FROM mullen_scores
                WHERE mullen_assessments_id = ? AND domain = ?
                ORDER BY id
                LIMIT 1
                """,
                (assessment_id, domain),
            ).fetchone()

            if existing_score:
                connection.execute(
                    """
                    UPDATE mullen_scores
                    SET raw_score = ?,
                        t_score = ?,
                        band_of_error = ?,
                        percentile_rank = ?,
                        descriptive_category = ?,
                        age_equivalence = ?
                    WHERE id = ?
                    """,
                    [*values, existing_score["id"]],
                )
            else:
                connection.execute(
                    """
                    INSERT INTO mullen_scores (
                        mullen_assessments_id,
                        domain,
                        raw_score,
                        t_score,
                        band_of_error,
                        percentile_rank,
                        descriptive_category,
                        age_equivalence
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [assessment_id, domain, *values],
                )


def get_mullen_assessment(patient_id: int) -> dict:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ms.*
            FROM mullen_scores ms
            JOIN mullen_assessments ma
              ON ma.id = ms.mullen_assessments_id
            WHERE ma.patient_id = ?
            ORDER BY ms.id
            """,
            (patient_id,),
        ).fetchall()

    return {row["domain"]: dict(row) for row in rows}


# Telephone Screening
def save_telephone_screening(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("telephone_screenings", patient_id, data)

def get_telephone_screening(patient_id: int) -> dict | None:
    return _get_one_to_one_form("telephone_screenings", patient_id)


# Questionaire Screening
def save_screening_questionnaire(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("screening_questionnaires", patient_id, data)

def get_screening_questionnaire(patient_id: int) -> dict | None:
    return _get_one_to_one_form("screening_questionnaires", patient_id)

# Medical History
def save_medical_history(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("medical_histories", patient_id, data)

def get_medical_history(patient_id: int) -> dict | None:
    return _get_one_to_one_form("medical_histories", patient_id)

# Family Medical History
def save_family_medical_history(patient_id: int, data: dict) -> None:
    _save_one_to_one_form("family_medical_histories", patient_id, data)

def get_family_medical_history(patient_id: int) -> dict | None:
    return _get_one_to_one_form("family_medical_histories", patient_id)

SIBLING_FIELDS = (
    "name",
    "age",
    "same_bio_father",
    "same_bio_mother",
    "adopted",
    "diagnosis",
)

def save_siblings(patient_id: int, siblings: list[dict]) -> None:
    """Replace this patient's siblings with the given list.

    Deleting then inserting is simpler than matching up edited rows, and
    doing both on one connection means a failure leaves the old rows in place.
    """
    columns = ", ".join(SIBLING_FIELDS)
    placeholders = ", ".join("?" for _ in SIBLING_FIELDS)

    with get_connection() as connection:
        connection.execute("DELETE FROM siblings WHERE patient_id = ?", (patient_id,))
        for sibling in siblings:
            connection.execute(
                f"INSERT INTO siblings (patient_id, {columns}) VALUES (?, {placeholders})",
                [patient_id, *(sibling.get(field) for field in SIBLING_FIELDS)],
            )

def list_siblings(patient_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT {', '.join(SIBLING_FIELDS)} FROM siblings WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        ).fetchall()

    return [dict(row) for row in rows]

HIGH_RISK = 1
LOW_RISK = 0

def familial_risk(answers: dict, siblings: list[dict]) -> tuple[int | None, str]:
    """Suggest the baby's familial risk from the Family Medical History answers.

    Returns (risk, reason), where risk is HIGH_RISK (1), LOW_RISK (0), or None.

    The lab's rule:
    - High: an older sibling has been diagnosed with ASD (question 4 is Yes).
      Other relatives (cousins, aunts...) don't count.
    - Low: no diagnosis anywhere in the family. Question 1 (psychiatric diagnosis
      in parents or full siblings) is No, no sibling has ASD or ADHD, and no row
      in the siblings table lists a diagnosis. Having siblings isn't required.
    - None: not enough answers yet, or the family fits neither rule.

    This is only a suggestion. The RA still sets risk on the Telephone Screening tab.
    """
    has_siblings = answers.get("has_siblings")
    if has_siblings == 1 and answers.get("sibling_autism") == 1:
        return HIGH_RISK, "A sibling has been diagnosed with ASD."

    needed = [answers.get("family_psychiatric"), has_siblings]
    if has_siblings == 1:
        needed += [answers.get("sibling_autism"), answers.get("sibling_adhd")]
    if None in needed:
        return None, "Answer questions 1 and 3 (and 4 and 5 if there are siblings) to see a suggestion."

    has_any_diagnosis = (
        answers.get("family_psychiatric") == 1
        or answers.get("sibling_adhd") == 1
        or any(sibling.get("diagnosis") for sibling in siblings)
    )
    if has_any_diagnosis:
        return None, (
            "Neither high nor low: a family member has a diagnosis other than a "
            "sibling with ASD. Check with the coordinator."
        )
    return LOW_RISK, "No one in the family has a diagnosis."

def sibling_relation(same_father: int | None, same_mother: int | None) -> str:
    """Work out a sibling's relationship from the two "same parent" answers.

    Each answer is 1 (Yes), 0 (No), or None (unknown). The result is worked out
    when needed rather than stored, so it can never disagree with the answers.
    """
    if same_father is None or same_mother is None:
        return "Unknown"
    if same_father == 1 and same_mother == 1:
        return "Full"
    if same_father == 1 or same_mother == 1:
        return "Half"
    return "Not biological"


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
    "Mullen Assessment":("mullen_assessment", "Mullen Assessment")
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
