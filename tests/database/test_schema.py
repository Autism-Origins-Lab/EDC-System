# tests/database/test_schema.py
from app.database.connection import get_connection
from app.database.migrations.runner import (
    CURRENT_SCHEMA_VERSION,
    MIGRATIONS,
    get_schema_version,
)


def test_database_initialization_creates_expected_tables(temp_database):
    expected = {
        "patients",
        "patients_video",
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


def test_migration_registry_is_contiguous_and_ordered():
    versions = [migration.VERSION for migration in MIGRATIONS]

    assert versions == list(range(1, CURRENT_SCHEMA_VERSION + 1))
    assert all(callable(migration.upgrade) for migration in MIGRATIONS)
