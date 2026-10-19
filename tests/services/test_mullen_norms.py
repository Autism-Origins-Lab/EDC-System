"""Regression examples checked against the user's C1/C2 source scans."""

import pytest

from app.services import mullen_scoring as scoring
from app.services.mullen_norms import (
    C1_TABLE,
    C2_CATEGORIES,
    C2_PERCENTILES,
    SCALE_DOMAINS,
)


def score(
    raw,
    birthday="2025-01-01",
    tested_on="2025-01-01",
    domain="gross_motor",
    confidence=90,
):
    return scoring.auto_score(
        raw,
        birthday,
        domain=domain,
        assessment_date=tested_on,
        confidence_level=confidence,
        age_calculation="calendar",
    )


# Raw score 3 across all columns and all four printed age bands.
# Expected T scores and percentiles were read separately from C1 and C2.
@pytest.mark.parametrize(
    ("tested_on", "t_scores", "percentiles"),
    [
        ("2025-01-01", (48, 51, 50, 52, 55), (42, 54, 50, 58, 69)),
        ("2025-03-01", (37, 38, 40, 44, 46), (10, 12, 16, 27, 34)),
        ("2025-04-01", (31, 33, 34, 35, 41), (3, 4, 5, 7, 18)),
        ("2025-05-01", (24, 27, 28, 28, 34), (1, 1, 1, 1, 5)),
    ],
)
def test_source_examples_across_scales(tested_on, t_scores, percentiles):
    for domain, t_score, percentile in zip(SCALE_DOMAINS, t_scores, percentiles, strict=True):
        result = score(3, tested_on=tested_on, domain=domain)
        assert result["t_score"] == t_score
        assert result["percentile_rank"] == percentile
        assert result["age_equivalence"] is None


@pytest.mark.parametrize(
    ("birthday", "tested_on", "raw_score", "expected"),
    [
        ("2025-02-01", "2025-03-31", 6, 66),  # 1 month 30 days
        ("2025-01-01", "2025-03-01", 6, 57),  # 2 months 0 days
        ("2025-01-01", "2025-03-31", 6, 57),  # 2 months 30 days
        ("2025-01-01", "2025-04-01", 6, 50),  # 3 months 0 days
        ("2025-02-01", "2025-05-31", 6, 50),  # 3 months 30 days
        ("2025-01-01", "2025-05-01", 6, 43),  # 4 months 0 days
        ("2025-01-01", "2025-05-31", 6, 43),  # 4 months 30 days
    ],
)
def test_source_age_band_boundaries(birthday, tested_on, raw_score, expected):
    assert score(raw_score, birthday, tested_on)["t_score"] == expected


@pytest.mark.parametrize(
    "tested_on", ["2025-01-01", "2025-03-01", "2025-04-01", "2025-05-01"]
)
@pytest.mark.parametrize(
    ("domain", "width90", "width95"),
    [
        ("gross_motor", 9, 11),
        ("visual_reception", 8, 10),
        ("fine_motor", 9, 10),
        ("receptive_language", 10, 12),
        ("expressive_language", 8, 10),
    ],
)
def test_source_confidence_widths(tested_on, domain, width90, width95):
    result90 = score(3, tested_on=tested_on, domain=domain, confidence=90)
    result95 = score(3, tested_on=tested_on, domain=domain, confidence=95)
    assert result90["band_of_error"] == width90
    assert result95["band_of_error"] == width95
    assert result90["t_score"] == result95["t_score"]
    assert result90["percentile_rank"] == result95["percentile_rank"]


@pytest.mark.parametrize(
    ("t_score", "percentile", "category"),
    [
        (80, 99, "Very High"),
        (70, 98, "Very High"),
        (69, 97, "Above Average"),
        (61, 86, "Above Average"),
        (60, 84, "Average"),
        (40, 16, "Average"),
        (39, 14, "Below Average"),
        (31, 3, "Below Average"),
        (30, 2, "Very Low"),
        (20, 1, "Very Low"),
        (67, 96, "Above Average"),
        (68, 96, "Above Average"),
        (28, 1, "Very Low"),
        (29, 2, "Very Low"),
    ],
)
def test_c2_source_boundaries_and_repeated_ranks(t_score, percentile, category):
    assert C2_PERCENTILES[t_score] == percentile
    matches = [label for low, high, label in C2_CATEGORIES if low <= t_score <= high]
    assert matches == [category]


def test_transcription_has_complete_printed_rows_and_c2_coverage():
    assert set(C2_PERCENTILES) == set(range(20, 81))
    for table, max_raw in zip(C1_TABLE, (9, 10, 11, 12), strict=True):
        assert set(table["rows"]) == set(range(max_raw + 1))
        for values in table["rows"].values():
            assert len(values) == 5
            assert all(value in C2_PERCENTILES for value in values)


def test_source_zero_floor_and_upper_limit():
    assert score(0)["t_score"] == 26
    assert score(0, tested_on="2025-03-01")["t_score"] == 20
    assert score(9)["t_score"] == 80
    with pytest.raises(scoring.MullenScoringError, match="No handbook conversion"):
        score(10)  # Do not extrapolate beyond the birth-to-1:30 printed table.


def test_ages_beyond_supplied_c1_page_are_unsupported():
    with pytest.raises(scoring.MullenScoringError, match="No handbook age band"):
        score(3, tested_on="2025-06-01")


@pytest.mark.parametrize("confidence", [None, True, 90.0, 80, 99, "95"])
def test_confidence_must_be_one_of_the_two_printed_levels(confidence):
    with pytest.raises(scoring.MullenScoringError, match="Confidence level"):
        score(3, confidence=confidence)


def test_missing_age_convention_still_requires_configuration(monkeypatch):
    monkeypatch.setattr(scoring, "AGE_CALCULATION", None)
    with pytest.raises(scoring.MullenScoringError, match="AGE_CALCULATION"):
        scoring.auto_score(
            3,
            "2025-01-01",
            domain="gross_motor",
            assessment_date="2025-03-01",
            confidence_level=90,
        )
