import csv

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QPushButton

from app.database.connection import get_connection
from app.database.schema import initialize_database
from app.ui.views.patients_view import PatientsView


@pytest.fixture
def patients_view_database(monkeypatch, tmp_path):
    # Build the current schema directly to isolate the db.
    from app import config

    database_path = tmp_path / "patients_view.db"
    monkeypatch.setattr(config, "DATABASE_PATH", database_path)
    initialize_database()
    return database_path


def _add_patient(
    subject_id: str,
    child_name: str,
    *,
    eligibility: str,
    comment: str,
    screener: str,
    schedule_date: str,
    form_status: str = "Pending",
) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO patients (subject_id, child_name, form_status)
            VALUES (?, ?, ?)
            """,
            (subject_id, child_name, form_status),
        )
        connection.execute(
            """
            INSERT INTO telephone_screenings (
                patient_id, eligibility, eligibility_comment, screener, schedule_date
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (cursor.lastrowid, eligibility, comment, screener, schedule_date),
        )


def _export_csv(view, qtbot, monkeypatch, output_path):
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(output_path), "CSV Files (*.csv)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *_args: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args: None)

    export_button = next(
        button
        for button in view.findChildren(QPushButton)
        if button.text() == "Export CSV"
    )
    qtbot.mouseClick(export_button, Qt.MouseButton.LeftButton)

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _displayed_rows(view):
    rows = {}
    for row_index in range(view.table.rowCount()):
        rows[view.table.item(row_index, 0).text()] = {
            "subject_id": view.table.item(row_index, 0).text(),
            "child_name": view.table.item(row_index, 1).text(),
            "eligibility": view.table.item(row_index, 2).text(),
            "screener": view.table.item(row_index, 3).text(),
            "schedule_date": view.table.item(row_index, 4).text(),
            "comment": view.table.item(row_index, 5).text(),
        }
    return rows


def test_export_csv_matches_patients_displayed_in_table(
    patients_view_database, qtbot, monkeypatch, tmp_path
):
    _add_patient(
        "SUB-101",
        "Avery Example",
        eligibility="Yes",
        comment="",
        screener="Jordan Staff",
        schedule_date="2026-10-14",
        form_status="Complete",
    )
    _add_patient(
        "SUB-102",
        "Riley Example",
        eligibility="No",
        comment="Outside eligibility range",
        screener="Casey Staff",
        schedule_date="2026-10-20",
    )

    view = PatientsView()
    qtbot.addWidget(view)
    displayed_rows = _displayed_rows(view)
    exported_rows = _export_csv(view, qtbot, monkeypatch, tmp_path / "patients.csv")

    assert {row["subject_id"] for row in exported_rows} == set(displayed_rows)
    assert len(exported_rows) == len(displayed_rows)
    for exported in exported_rows:
        displayed = displayed_rows[exported["subject_id"]]
        for field in (
            "subject_id",
            "child_name",
            "eligibility",
            "comment",
            "screener",
            "schedule_date",
        ):
            assert exported[field] == displayed[field]

        patient_data = next(
            patient
            for patient in view.patients
            if patient["subject_id"] == exported["subject_id"]
        )
        assert exported["form_status"] == patient_data["form_status"]


def test_export_csv_contains_only_patients_matching_search_filter(
    patients_view_database, qtbot, monkeypatch, tmp_path
):
    _add_patient(
        "SUB-201",
        "Keep Avery",
        eligibility="Yes",
        comment="",
        screener="Jordan Staff",
        schedule_date="2026-10-14",
    )
    _add_patient(
        "SUB-202",
        "Keep Riley",
        eligibility="Pending",
        comment="",
        screener="Casey Staff",
        schedule_date="2026-10-20",
    )
    _add_patient(
        "SUB-203",
        "Hide Morgan",
        eligibility="No",
        comment="Not eligible",
        screener="Taylor Staff",
        schedule_date="2026-10-22",
    )

    view = PatientsView()
    qtbot.addWidget(view)
    view.set_search_text("Keep")
    displayed_rows = _displayed_rows(view)
    exported_rows = _export_csv(view, qtbot, monkeypatch, tmp_path / "filtered.csv")

    assert len(displayed_rows) == 2
    exported_subject_ids = {row["subject_id"] for row in exported_rows}
    assert exported_subject_ids == set(displayed_rows)
    assert "SUB-203" not in exported_subject_ids
