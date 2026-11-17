import sqlite3

VERSION = 9
NAME = "number separate Mullen summaries and track save order"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(mullen_assessments)")}
    for column in ("assessment_number", "saved_order"):
        if column not in columns:
            connection.execute(
                f"ALTER TABLE mullen_assessments ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0"
            )
    patients = connection.execute("SELECT DISTINCT patient_id FROM mullen_assessments").fetchall()
    for (patient_id,) in patients:
        rows = connection.execute(
            "SELECT id FROM mullen_assessments WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        ).fetchall()
        for number, (assessment_id,) in enumerate(rows, 1):
            connection.execute(
                "UPDATE mullen_assessments SET assessment_number = ? "
                "WHERE id = ? AND assessment_number = 0", (number, assessment_id),
            )
        rows = connection.execute(
            "SELECT id FROM mullen_assessments WHERE patient_id = ? ORDER BY updated_at, id",
            (patient_id,),
        ).fetchall()
        for order, (assessment_id,) in enumerate(rows, 1):
            connection.execute(
                "UPDATE mullen_assessments SET saved_order = ? WHERE id = ? AND saved_order = 0",
                (order, assessment_id),
            )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS mullen_summary_number "
        "ON mullen_assessments(patient_id, assessment_number)"
    )
