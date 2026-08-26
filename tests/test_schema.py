# tests/test_schema.py
from app.database.connection import get_connection
from app.database.migration import CURRENT_SCHEMA_VERSION, get_schema_version


def test_database_initialization_creates_expected_tables(temp_database):
    expected = {
        "patients",
        "telephone_screenings",
        "screening_questionnaires",
        "medical_histories",
        "family_medical_histories",
        "procedure_schedules",
        "export_logs",
    }

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    assert expected.issubset({row["name"] for row in rows})

def test_database_initialization_sets_schema_version(temp_database):
    with get_connection() as connection:
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION