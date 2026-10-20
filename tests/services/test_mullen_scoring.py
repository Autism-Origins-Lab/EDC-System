"""Scoring-engine tests use synthetic values, never clinical norms."""

from datetime import date

import pytest

from app.services import mullen_scoring as scoring


@pytest.mark.parametrize(
    ("birthday", "tested_on", "convention", "expected"),
    [
        ("2025-01-01", "2025-03-01", "calendar", (2, 0)),
        ("2025-01-01", "2025-03-31", "calendar", (2, 30)),
        ("2025-01-01", "2025-04-01", "calendar", (3, 0)),
        ("2025-01-31", "2025-02-28", "calendar", (1, 0)),
        ("2024-01-31", "2024-02-29", "calendar", (1, 0)),
        ("2024-02-29", "2025-02-28", "calendar", (12, 0)),
        ("2025-01-15", "2025-03-10", "calendar", (1, 23)),
        ("2025-01-15", "2025-03-10", "30_day_borrow", (1, 25)),
        (date(2025, 1, 15), date(2025, 1, 15), "calendar", (0, 0)),
    ],
)
def test_age_conventions(birthday, tested_on, convention, expected):
    assert scoring.calculate_age(birthday, tested_on, convention=convention) == expected


@pytest.mark.parametrize(
    ("birthday", "tested_on", "convention", "message"),
    [
        ("", "2025-03-01", "calendar", "Date of birth"),
        ("2025-02-30", "2025-03-01", "calendar", "Date of birth"),
        ("2025-01-01", "invalid", "calendar", "Assessment date"),
        ("2025-03-02", "2025-03-01", "calendar", "cannot precede"),
        ("2025-01-01", "2025-03-01", None, "AGE_CALCULATION"),
        ("2025-01-01", "2025-03-01", "unknown", "AGE_CALCULATION"),
    ],
)
def test_invalid_age_inputs(birthday, tested_on, convention, message, monkeypatch):
    monkeypatch.setattr(scoring, "AGE_CALCULATION", None)
    with pytest.raises(scoring.MullenScoringError, match=message):
        scoring.calculate_age(birthday, tested_on, convention=convention)


@pytest.fixture
def synthetic_norms(monkeypatch):
    result = {
        "t_score": 41,
        "band_of_error": {90: 2.5, 95: 3},
        "percentile_rank": "<1",
        "descriptive_category": "Synthetic test category",
        "age_equivalence": None,
    }
    bands = [
        {"min_age": (2, 0), "max_age": (2, 30), "scores": {0: result}},
        {
            "min_age": (3, 0),
            "max_age": (3, 30),
            "scores": {0: {**result, "t_score": 42}},
        },
    ]
    monkeypatch.setattr(scoring, "AGE_CALCULATION", "calendar")
    monkeypatch.setattr(scoring, "MULLEN_NORMS", {"gross_motor": bands})
    return bands


def score(raw_score=0, tested_on="2025-03-01", domain="gross_motor"):
    return scoring.auto_score(
        raw_score,
        "2025-01-01",
        domain=domain,
        assessment_date=tested_on,
        confidence_level=90,
    )


@pytest.mark.parametrize(
    ("tested_on", "expected"),
    [("2025-03-01", 41), ("2025-03-31", 41), ("2025-04-01", 42)],
)
def test_inclusive_age_bands_and_zero_score(synthetic_norms, tested_on, expected):
    assert score(tested_on=tested_on)["t_score"] == expected


def test_result_preserves_qualifiers_and_does_not_mutate_norms(synthetic_norms):
    result = score()
    assert result["percentile_rank"] == "<1"
    result["t_score"] = 999
    assert score()["t_score"] == 41


@pytest.mark.parametrize("raw_score", [-1, True, 1.5, "0", None])
def test_invalid_raw_scores(synthetic_norms, raw_score):
    with pytest.raises(scoring.MullenScoringError, match="non-negative integer"):
        score(raw_score)


def test_unknown_domain(synthetic_norms):
    with pytest.raises(scoring.MullenScoringError, match="Unknown Mullen domain"):
        score(domain="not_a_scale")


def test_missing_norms(monkeypatch):
    monkeypatch.setattr(scoring, "MULLEN_NORMS", {"gross_motor": []})
    with pytest.raises(scoring.MullenScoringError, match="Add handbook"):
        scoring.auto_score(
            0,
            "2025-01-01",
            domain="gross_motor",
            assessment_date="2025-03-01",
            confidence_level=90,
            age_calculation="calendar",
        )


def test_missing_raw_score_is_not_interpolated(synthetic_norms):
    with pytest.raises(scoring.MullenScoringError, match="No handbook conversion"):
        score(1)


def test_age_outside_configured_bands(synthetic_norms):
    with pytest.raises(scoring.MullenScoringError, match="No handbook age band"):
        score(tested_on="2025-05-01")


def test_incomplete_conversion(synthetic_norms):
    synthetic_norms[0]["scores"][0]["t_score"] = None
    with pytest.raises(scoring.MullenScoringError, match="all four"):
        score()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("min_age", None, "min_age"),
        ("min_age", (2, 31), "days from 0 to 30"),
        ("min_age", (3, 0), "cannot exceed"),
        ("scores", None, "raw-score dictionary"),
        ("scores", {False: {}}, "lookup keys"),
    ],
)
def test_malformed_band(synthetic_norms, field, value, message):
    synthetic_norms[0][field] = value
    with pytest.raises(scoring.MullenScoringError, match=message):
        score()


def test_overlapping_age_bands_are_rejected(synthetic_norms):
    synthetic_norms[1]["min_age"] = (2, 30)
    with pytest.raises(scoring.MullenScoringError, match="Overlapping"):
        score()
