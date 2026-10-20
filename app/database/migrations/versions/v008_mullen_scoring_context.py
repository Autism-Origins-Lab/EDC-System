import sqlite3

VERSION = 8
NAME = "persist Mullen scoring context"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(mullen_assessments)")
    }
    for name, kind in (
        ("assessment_date", "TEXT"),
        ("scoring_date_of_birth", "TEXT"),
        ("confidence_level", "INTEGER"),
        ("age_calculation", "TEXT"),
    ):
        if name not in columns:
            connection.execute(
                f"ALTER TABLE mullen_assessments ADD COLUMN {name} {kind}"
            )
