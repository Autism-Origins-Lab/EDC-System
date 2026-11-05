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
            "startup_page": "Settings",
            "confirm_delete": False,
        },
        path,
    )

    assert load_preferences(path) == saved
    path.write_text(json.dumps({"theme": "Unsupported"}), encoding="utf-8")
    assert load_preferences(path) == DEFAULT_PREFERENCES


def test_dates_display_as_mm_dd_yyyy_and_store_as_iso():
    assert format_date("2026-10-06") == "10-06-2026"
    assert parse_date("10-06-2026") == "2026-10-06"
    assert parse_date("") == ""
