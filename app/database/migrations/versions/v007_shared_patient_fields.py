import sqlite3

VERSION = 7
NAME = "synchronize shared patient fields"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(telephone_screenings)")
    }
    for field in ("high_familial_risk", "low_familial_risk"):
        if field not in columns:
            connection.execute(
                f"ALTER TABLE telephone_screenings ADD COLUMN {field} INTEGER"
            )

    # Retain existing patient values; recover missing identity from older questionnaires.
    for field in ("child_name", "date_of_birth", "sex", "race"):
        connection.execute(
            f"""
            UPDATE patients SET {field} = (
                SELECT sq.{field} FROM screening_questionnaires sq
                WHERE sq.patient_id = patients.id
            )
            WHERE TRIM(COALESCE({field}, '')) = ''
              AND EXISTS (
                SELECT 1 FROM screening_questionnaires sq
                WHERE sq.patient_id = patients.id
                  AND TRIM(COALESCE(sq.{field}, '')) <> ''
              )
            """
        )
        connection.execute(
            f"""
            UPDATE screening_questionnaires SET {field} = (
                SELECT p.{field} FROM patients p WHERE p.id = patient_id
            )
            """
        )

    connection.execute(
        """
        UPDATE patients SET risk = (
            SELECT CASE
                WHEN ts.high_familial_risk = 1
                  AND COALESCE(ts.low_familial_risk, 0) = 0 THEN 1
                WHEN ts.low_familial_risk = 1
                  AND COALESCE(ts.high_familial_risk, 0) = 0 THEN 0
                ELSE NULL END
            FROM telephone_screenings ts WHERE ts.patient_id = patients.id
        ) WHERE risk IS NULL
        """
    )
    if "atRisk" in columns:
        connection.execute(
            """
            UPDATE patients SET risk = (
                SELECT ts.atRisk FROM telephone_screenings ts
                WHERE ts.patient_id = patients.id
            ) WHERE risk IS NULL AND EXISTS (
                SELECT 1 FROM telephone_screenings ts
                WHERE ts.patient_id = patients.id
                  AND ts.high_familial_risk IS NULL
                  AND ts.low_familial_risk IS NULL
                  AND ts.atRisk IN (0, 1)
            )
            """
        )
    connection.execute(
        """
        UPDATE telephone_screenings SET
            high_familial_risk = COALESCE(
                (SELECT risk = 1 FROM patients WHERE id = patient_id), 0
            ),
            low_familial_risk = COALESCE(
                (SELECT risk = 0 FROM patients WHERE id = patient_id), 0
            )
        """
    )
