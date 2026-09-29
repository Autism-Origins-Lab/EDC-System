import pytest

from app import config
from app.database.connection import get_connection
from app.database.queries.forms import get_telephone_screening, save_telephone_screening
from app.database.queries.patients import create_patient, get_patient
from app.database.schema import initialize_database
from app.ui.views.telephone_screening_view import TelephoneScreeningView


@pytest.fixture
def risk_database(monkeypatch, tmp_path):
    # Build the current schema directly to isolate save behavior from migrations.
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "risk.db")
    initialize_database()


def test_risk_clicks_save_and_reload(qtbot, monkeypatch, risk_database):
    monkeypatch.setattr(
        "app.ui.views.telephone_screening_view.QMessageBox.information",
        lambda *args: None,
    )
    patient_id = create_patient("RISK-TEST")
    other_id = create_patient("OTHER-PATIENT")
    view = TelephoneScreeningView(patient_id)
    qtbot.addWidget(view)

    for selection, expected in [("high", 1), ("low", 0), ("high", 1), ("high", None)]:
        getattr(view, f"{selection}_risk_checkbox").click()
        with qtbot.waitSignal(view.screening_saved):
            view.save_button.click()

        assert get_patient(patient_id)["risk"] == expected
        assert get_patient(other_id)["risk"] is None
        reloaded = TelephoneScreeningView(patient_id)
        qtbot.addWidget(reloaded)
        assert reloaded.high_risk_checkbox.isChecked() == (expected == 1)
        assert reloaded.low_risk_checkbox.isChecked() == (expected == 0)


def test_partial_screening_update_preserves_risk(risk_database):
    patient_id = create_patient("PARTIAL")
    save_telephone_screening(patient_id, {"high_familial_risk": 1, "low_familial_risk": 0})
    save_telephone_screening(patient_id, {"screener": "Test"})
    assert get_patient(patient_id)["risk"] == 1


def test_conflicting_risk_rolls_back_screening(risk_database):
    patient_id = create_patient("CONFLICT")
    save_telephone_screening(patient_id, {"high_familial_risk": 1, "low_familial_risk": 0})
    with pytest.raises(ValueError, match="not both"):
        save_telephone_screening(patient_id, {"low_familial_risk": 1})
    assert get_patient(patient_id)["risk"] == 1
    assert get_telephone_screening(patient_id)["low_familial_risk"] == 0


def test_patient_update_failure_rolls_back_screening(risk_database):
    patient_id = create_patient("ROLLBACK")
    save_telephone_screening(patient_id, {"high_familial_risk": 1, "low_familial_risk": 0})
    with get_connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_risk BEFORE UPDATE OF risk ON patients "
            "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
        )
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError, match="test failure"):
        save_telephone_screening(patient_id, {"high_familial_risk": 0, "low_familial_risk": 1})
    assert get_patient(patient_id)["risk"] == 1
    assert get_telephone_screening(patient_id)["high_familial_risk"] == 1
