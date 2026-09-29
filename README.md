# EDC System

Electronic Data Capture desktop application for managing study participants, screening forms, medical history forms, procedure schedules, and local study data exports.

The application is a Python/PySide6 desktop app backed by a local SQLite database.

## Current Features

- Patient dashboard with search, patient metrics, and a table of participant records.
- New patient creation with unique Subject ID validation.
- Patient detail dialog with tabs for:
  - Overview
  - Telephone Screening
  - Screening Questionnaire
  - Medical History
  - Family Medical History
  - Procedure Schedule
- SQLite-backed save/load helpers for patient records and form data.
- Versioned database migrations using SQLite `PRAGMA user_version`.
- Backend Excel export support for core database tables.
- Backend video-record helpers for associating video file paths with patients.

Some sidebar sections are placeholders while the core forms and workflows are being migrated.

## Project Structure

```text
app/
  main.py                     Application entrypoint
  config.py                   App paths and local database location
  database/
    connection.py             SQLite connection context manager
    schema.py                 Full database schema for new databases
    migration.py              Versioned migrations for existing databases
    queries/
      patients.py             Patient create/read/update/search queries
      forms.py                Form and procedure schedule queries
      videos.py               Patient video path queries
      exports.py              Excel workbook export helper
  ui/
    main_window.py            Main PySide6 window
    sidebar.py                Sidebar navigation
    topbar.py                 Top navigation/header
    theme.py                  Qt stylesheet
    views/                    Patient dashboard, dialogs, and form tabs

tests/                        Pytest coverage for schema, patient queries, forms, and exports
OLD-SYSTEM/                   Legacy CSV-to-SQL prototype and sample data
```

## Requirements

- Python 3.13 or compatible Python 3.x environment
- PySide6
- pandas
- numpy
- openpyxl
- pytest
- pytest-qt
- ruff

Install the pinned dependencies with:

```powershell
pip install -r requirements.txt
```

## Running The App

From the repository root:

```powershell
cd C:\Users\kevin\EDC-System
$env:PYTHONPATH="."
python -m app.main
```

On startup, the app runs database migrations before opening the main window.

## Database

The local SQLite database is stored at:

```text
data/patient_data.db
```

Local database files are ignored by Git.

The schema is centered on the `patients` table. Related tables use `patient_id` foreign keys with `ON DELETE CASCADE` so records stay tied to their patient:

- `patients`
- `patients_video`
- `telephone_screenings`
- `screening_questionnaires`
- `medical_histories`
- `family_medical_histories`
- `procedure_schedules`
- `export_logs`

Most form tables are one row per patient. Procedure schedules allow one row per patient/procedure pair. Patient videos allow multiple video records per patient.

## Running Tests

From the repository root:

```powershell
$env:PYTHONPATH="."
pytest
```

Run a smaller database-focused set:

```powershell
$env:PYTHONPATH="."
pytest tests/test_schema.py tests/test_patient_queries.py tests/test_form_queries.py tests/test_exports.py
```

## Development Notes

- Use `schema.py` for the full schema expected by a brand-new database.
- Use `migration.py` for incremental changes needed by already-existing databases.
- Use query modules under `app/database/queries/` as the UI-facing data access layer.
- The app currently stores data locally only; no remote database or account service is configured.
- `OLD-SYSTEM/` is kept as a reference for the previous CSV-to-SQL import work.
