"""Persistence and formatting helpers for local application preferences."""

import json
from datetime import date, datetime
from pathlib import Path

from app import config

DEFAULT_PREFERENCES = {
    "theme": "Light",
    "startup_page": "Patients",
    "confirm_delete": True,
    "warn_unsaved_changes": True,
    "backup_directory": "",
}

PREFERENCE_OPTIONS = {
    "theme": {"Light", "Dark"},
    "startup_page": {"Patients", "Imports", "Exports", "Settings"},
}


def normalize_preferences(values: dict | None) -> dict:
    """Return a complete, validated preference dictionary."""
    preferences = DEFAULT_PREFERENCES.copy()
    if not isinstance(values, dict):
        return preferences

    for key, options in PREFERENCE_OPTIONS.items():
        if values.get(key) in options:
            preferences[key] = values[key]
    for key in ("confirm_delete", "warn_unsaved_changes"):
        if isinstance(values.get(key), bool):
            preferences[key] = values[key]
    directory = values.get("backup_directory")
    if isinstance(directory, str) and "\0" not in directory:
        preferences["backup_directory"] = directory.strip()
    return preferences


def load_preferences(path: Path | None = None) -> dict:
    """Load local preferences, falling back safely when the file is absent or invalid."""
    settings_path = path or config.PREFERENCES_PATH
    try:
        values = json.loads(settings_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        values = None
    return normalize_preferences(values)


def save_preferences(values: dict, path: Path | None = None) -> dict:
    """Validate and atomically save preferences to the local data directory."""
    preferences = normalize_preferences(values)
    settings_path = path or config.PREFERENCES_PATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = settings_path.with_suffix(f"{settings_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(preferences, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(settings_path)
    return preferences


# Every date in the app is shown as MM-DD-YYYY. Fixed format rather than a preference.
# database keeps YYYY-MM-DD bc that's more standard for exports/sheets
DATE_FORMAT = "MM-DD-YYYY"
_DISPLAY_PATTERN = "%m-%d-%Y"


def format_date(value: str | None) -> str:
    """Format a stored ISO date for display, leaving non-date values untouched."""
    if not value:
        return ""
    try:
        return date.fromisoformat(value).strftime(_DISPLAY_PATTERN)
    except ValueError:
        return value


def parse_date(value: str) -> str:
    """Convert a user-entered MM-DD-YYYY date to the ISO form stored in SQLite."""
    cleaned_value = value.strip()
    if not cleaned_value:
        return ""
    try:
        return datetime.strptime(cleaned_value, _DISPLAY_PATTERN).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Enter the date as {DATE_FORMAT}.") from exc
