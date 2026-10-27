# EDC System

Electronic Data Capture desktop application for managing study participants, screening forms, medical history forms, procedure schedules, and local study data exports.

The application is a Python/PySide6 desktop app backed by a local SQLite database.

## Current Features

- Patient dashboard with search, patient metrics, and a table of participant records.
- New patient creation with unique Subject ID validation.
- Guided patient workspace with a non-clickable section indicator and Back / Save and Continue controls for:
  - Overview
  - Telephone Screening
  - Screening Questionnaire
  - Medical History
  - Family Medical History
  - Procedure Schedule
  - Mullen Assessment
  - Video References
  - Review Answers
- Editable overview with shared participant identity and familial risk.
- Section saving before advancing, drafts retained when going back, and save/discard/cancel prompts when closing with edits.
- Final answer summary with blank answers displayed as N/A. Mark as Complete requires a screener name and is independent of eligibility. Saving edits to a completed record returns it to Pending for review.
- Optional Yes/No questions default to Not answered and retain three distinct stored states: unanswered, Yes, and No. Existing saved Yes/No values are preserved; historical No values cannot be automatically identified as previously unanswered.
- Persistent local settings for theme, table density, startup page, date display, and safety prompts.
- Patient deletion with cascading related-record cleanup and optional confirmation.
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
    migrations/
      runner.py               Orders and applies pending migrations
      versions/               Immutable migration modules (v001, v002, ...)
    repositories/
      patients.py             Patient create/read/update/search persistence
      forms.py                Form and procedure schedule persistence
      videos.py               Patient video path persistence
  services/
    exports.py                Excel workbook export service
    preferences.py            Local preference persistence and date formatting
  ui/
    main_window.py            Main PySide6 window
    theme.py                  Qt stylesheet
    components/               Shared sidebar and topbar components
    pages/                    Patient dashboard and settings pages
    dialogs/                  New-patient and patient-workspace dialogs
    forms/                    Patient overview, form, assessment, and video views

scripts/
  seed_database.py            Local fake-data seeding utility

tests/
  database/                   Schema, repository, and migration tests
  services/                   Export service tests
  ui/                         Page, dialog, and form tests
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

Application preferences are stored separately at `data/preferences.json`. This file is
also local-only and is ignored by Git; deleting it restores the built-in defaults.

### Database backup and recovery

Settings provides **Create Backup**, **Restore Backup**, and **Choose Backup Folder**.
The default backup folder is `data/backups/`. Choose a protected folder on a separate
device or storage system when protection against computer/drive failure is needed.

Starting the application creates a validated baseline snapshot. Committed database
changes request background snapshots; rapid requests are combined so copies do not
queue indefinitely. Reads and rolled-back saves do not request a backup. Automatic
backups retain the 20 most recent copies plus one per backup day for up to 30 backup
days. Manual backups and copies made before deletion, upgrade, or restore are never
automatically removed. Copies have unique UTC timestamps and are published only
after the SQLite backup API completes and validation succeeds.

Backups include every database table, patient/form relationships, saved Mullen
scoring context, completion statuses, and video references. Actual video files and
application preferences are separate and are not included. SQLite backup files
contain the same sensitive patient information as the live database and should be
stored with equivalent access protection; the app does not encrypt them.

Restore replaces the entire patient database; it does not merge individual records.
Close patient forms first. The application previews the selected file's date and
patient count, rejects damaged/unrelated/newer-version databases, checks integrity
and foreign keys, and upgrades supported older backups in a temporary working copy.
It preserves the current database before changing it. A damaged current database
is preserved as a ZIP containing its original database and journal files. Healthy
restores use SQLite's transactional backup API, including when WAL is enabled.
The selected backup is not modified. Restore success refreshes the patient list.

If the database cannot open during startup, recovery is available before the main
window appears. An initialization marker detects a missing/empty database in an
existing workspace so it is not silently replaced with an empty patient list.
A database lock prevents two application instances using the same database.
Backup errors are reported separately from save errors: an already committed save
remains saved if the backup destination is unavailable. Retry **Create Backup** in
Settings after correcting the destination. **Restore Defaults** preserves the chosen
backup folder. Recovery copies contain real data; remove them only when no longer
needed.

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
pytest tests/database/test_schema.py tests/database/test_patient_queries.py tests/database/test_form_queries.py tests/services/test_exports.py
```

## Development Notes

- Use `schema.py` for the full schema expected by a brand-new database.
- Add incremental database changes as a new immutable module under `app/database/migrations/versions/`.
- Register new migration modules in `app/database/migrations/runner.py`; never edit a migration that may already have run.
- Use repository modules under `app/database/repositories/` as the UI-facing data access layer.
- Keep export generation and other application operations under `app/services/`.
- The app currently stores data locally only; no remote database or account service is configured.
