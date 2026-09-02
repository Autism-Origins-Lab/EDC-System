import pytest


@pytest.fixture
def temp_database(monkeypatch, tmp_path):
    from app import config
    from app.database.migration import run_migrations

    database_path = tmp_path / "patient_data.db"
    monkeypatch.setattr(config, "DATABASE_PATH", database_path)
    run_migrations()
    return database_path
