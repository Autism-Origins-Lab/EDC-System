import json

from app.services.preferences import (
    DEFAULT_PREFERENCES,
    format_date,
    load_preferences,
    parse_date,
    save_preferences,
)


def test_preferences_round_trip_and_validate_unknown_values(tmp_path):
    path = tmp_path / "preferences.json"
    saved = save_preferences(
        {
            **DEFAULT_PREFERENCES,
            "theme": "Dark",
            "row_density": "Compact",
            "startup_page": "Settings",
            "date_format": "MM/DD/YYYY",
            "confirm_delete": False,
        },
        path,
    )

    assert load_preferences(path) == saved
    path.write_text(json.dumps({"theme": "Unsupported"}), encoding="utf-8")
    assert load_preferences(path) == DEFAULT_PREFERENCES


def test_date_formatting_uses_iso_storage():
    assert format_date("2026-10-06", "MM/DD/YYYY") == "10/06/2026"
    assert parse_date("10/06/2026", "MM/DD/YYYY") == "2026-10-06"
    assert format_date("2026-10-06", "YYYY-MM-DD") == "2026-10-06"
