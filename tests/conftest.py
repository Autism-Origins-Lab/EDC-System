import pytest


@pytest.fixture(autouse=True)
def isolated_preferences(monkeypatch, tmp_path):
    from app import config

    monkeypatch.setattr(config, "PREFERENCES_PATH", tmp_path / "preferences.json")


@pytest.fixture
def temp_database(monkeypatch, tmp_path):
    from app import config
    from app.database.migrations.runner import run_migrations

    database_path = tmp_path / "patient_data.db"
    monkeypatch.setattr(config, "DATABASE_PATH", database_path)
    run_migrations()
    return database_path
