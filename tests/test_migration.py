from app import config
from app.database.connection import get_connection
from app.database.migration import (
    CURRENT_SCHEMA_VERSION,
    SIBLING_TYPE_COLUMNS,
    SIBLINGS_SCHEMA_SQL,
    get_schema_version,
    migrate_telephone_screening_risk_columns,
    run_migrations,
)
from app.database.queries.forms import (
    get_telephone_screening,
    list_siblings,
    save_telephone_screening,
)
from app.database.queries.patients import create_patient
from app.database.schema import SCHEMA_SQL


def patient_columns() -> set[str]:
    with get_connection() as connection:
        rows = connection.execute("PRAGMA table_info(patients)").fetchall()
    return {row["name"] for row in rows}


def test_brand_new_database_migrates_without_errors(temp_database):
    # temp_database already ran run_migrations() on an empty file
    assert "form_status" in patient_columns()


def test_running_migrations_twice_is_safe(temp_database):
    run_migrations()
    with get_connection() as connection:
        assert get_schema_version(connection) == CURRENT_SCHEMA_VERSION


def test_old_version_1_database_gets_form_status(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "old.db")

    # Build a version 1 database from before form_status was in the schema
    old_schema = SCHEMA_SQL.replace("    form_status TEXT DEFAULT 'Pending',\n", "")
    assert old_schema != SCHEMA_SQL
    with get_connection() as connection:
        connection.executescript(old_schema)
        connection.execute("PRAGMA user_version = 1")
    assert "form_status" not in patient_columns()

    run_migrations()

    assert "form_status" in patient_columns()


def table_columns(table_name: str) -> set[str]:
    with get_connection() as connection:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def make_version_6_database() -> None:
    """Build a database the way a version 6 install looked: atRisk instead of
    the two risk columns, and none of the new family history sibling pieces."""
    schema = SCHEMA_SQL.replace(
        "    high_familial_risk INTEGER,\n    low_familial_risk INTEGER,\n",
        "    atRisk BOOLEAN,\n",
    )
    schema = schema.replace(SIBLINGS_SCHEMA_SQL.strip(), "")
    for column in SIBLING_TYPE_COLUMNS:
        schema = schema.replace(f"    {column} INTEGER,\n", "")

    with get_connection() as connection:
        connection.executescript(schema)
        connection.execute("PRAGMA user_version = 6")

    assert "high_familial_risk" not in table_columns("telephone_screenings")
    assert "sibling_autism_full" not in table_columns("family_medical_histories")
    assert table_columns("siblings") == set()  # the table doesn't exist yet


def test_version_6_database_gets_both_risk_columns(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "v6.db")
    make_version_6_database()

    run_migrations()

    assert {"high_familial_risk", "low_familial_risk"} <= table_columns("telephone_screenings")
    patient_id = create_patient("V6-PATIENT")
    save_telephone_screening(patient_id, {"high_familial_risk": 1, "low_familial_risk": 0})
    assert get_telephone_screening(patient_id)["high_familial_risk"] == 1


def test_version_6_database_gets_sibling_columns_and_table(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "v6.db")
    make_version_6_database()

    run_migrations()
    run_migrations()  # safe to run twice

    family_columns = table_columns("family_medical_histories")
    assert set(SIBLING_TYPE_COLUMNS) <= family_columns
    # The old paper question 6 columns stay in place
    assert {"same_father_as_older_sibling", "same_mother_as_older_sibling"} <= family_columns
    assert {"patient_id", "name", "age", "same_bio_father", "same_bio_mother",
            "adopted", "diagnosis"} <= table_columns("siblings")


def test_database_already_at_version_7_still_gets_siblings(monkeypatch, tmp_path):
    # Some databases ran version 7 (risk columns) before the sibling pieces existed
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "v7.db")
    make_version_6_database()
    with get_connection() as connection:
        migrate_telephone_screening_risk_columns(connection)
        connection.execute("PRAGMA user_version = 7")

    run_migrations()

    assert set(SIBLING_TYPE_COLUMNS) <= table_columns("family_medical_histories")
    patient_id = create_patient("V7-PATIENT")
    assert list_siblings(patient_id) == []
