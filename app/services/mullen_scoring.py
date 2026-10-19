from calendar import monthrange
from datetime import date
from itertools import pairwise

from app.services.mullen_norms import MULLEN_NORMS

AGE_CALCULATION: str | None = None

SCORE_FIELDS = (
    "t_score",
    "band_of_error",
    "percentile_rank",
    "descriptive_category",
    "age_equivalence",
)

# C1/C2 conversions live in mullen_norms.py. Age equivalents remain deferred.


class MullenScoringError(ValueError):
    """Invalid input, incomplete configuration, or unavailable conversion."""


def _parse_date(value: date | str, field_name: str) -> date:
    if type(value) is date:
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass

    raise MullenScoringError(
        f"{field_name} must be a date or YYYY-MM-DD string."
    )


def calculate_age(
    date_of_birth: date | str,
    assessment_date: date | str,
    *,
    convention: str | None = None,
) -> tuple[int, int]:
    """Return (total months, days) using the configured age convention.

    Calendar counts completed monthly birthdays, then elapsed days. A birthday
    outside a month is clamped to its final day (including February/leap years).
    30_day_borrow subtracts date components and borrows 30 days when needed.
    Choose a convention only after matching it to the handbook instructions.
    """
    birthday = _parse_date(date_of_birth, "Date of birth")
    tested_on = _parse_date(assessment_date, "Assessment date")

    if tested_on < birthday:
        raise MullenScoringError(
            "Assessment date cannot precede date of birth."
        )

    rule = AGE_CALCULATION if convention is None else convention

    months = (
        (tested_on.year - birthday.year) * 12
        + tested_on.month
        - birthday.month
    )

    if rule == "30_day_borrow":
        days = tested_on.day - birthday.day

        if days < 0:
            months -= 1
            days += 30

        return months, days

    if rule == "calendar":

        def anniversary(offset: int) -> date:
            year, month_index = divmod(
                birthday.year * 12 + birthday.month - 1 + offset,
                12,
            )
            month = month_index + 1

            return date(
                year,
                month,
                min(birthday.day, monthrange(year, month)[1]),
            )

        anchor = anniversary(months)

        if anchor > tested_on:
            months -= 1
            anchor = anniversary(months)

        return months, (tested_on - anchor).days

    raise MullenScoringError(
        'Set AGE_CALCULATION to "calendar" or "30_day_borrow" '
        "per the handbook."
    )


def _age_boundary(value: object, name: str) -> tuple[int, int]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise MullenScoringError(
            f"{name} must contain (total_months, days)."
        )

    months, days = value

    if (
        type(months) is not int
        or type(days) is not int
        or months < 0
        or not 0 <= days <= 30
    ):
        raise MullenScoringError(
            f"{name} requires months >= 0 and days from 0 to 30."
        )

    return months, days


def auto_score(
    raw_input: int,
    date_of_birth: date | str,
    *,
    domain: str,
    assessment_date: date | str,
    confidence_level: int,
    age_calculation: str | None = None,
) -> dict:
    """Return C1/C2 derived fields for a raw score and age at testing.

    Zero is valid. The UI should clear blank inputs without calling this function.
    Missing conversions raise MullenScoringError, never estimated results.
    Assessment date is required; reopening a record must not change its age.
    confidence_level must be 90 or 95. band_of_error is the positive width of
    the printed +/- band. age_equivalence is None until C4 is implemented.
    """
    if type(raw_input) is not int or raw_input < 0:
        raise MullenScoringError(
            "Raw score must be a non-negative integer."
        )

    if type(confidence_level) is not int or confidence_level not in (90, 95):
        raise MullenScoringError("Confidence level must be 90 or 95.")

    if not isinstance(domain, str) or domain not in MULLEN_NORMS:
        raise MullenScoringError(f"Unknown Mullen domain: {domain!r}.")

    age = calculate_age(
        date_of_birth,
        assessment_date,
        convention=age_calculation,
    )

    bands = MULLEN_NORMS[domain]

    if not isinstance(bands, list) or not bands:
        raise MullenScoringError(
            f"Add handbook age bands and conversions for {domain}."
        )

    configured = []

    for band in bands:
        if not isinstance(band, dict):
            raise MullenScoringError("Each age band must be a dictionary.")

        lower = _age_boundary(band.get("min_age"), "min_age")
        upper = _age_boundary(band.get("max_age"), "max_age")

        if lower > upper:
            raise MullenScoringError("min_age cannot exceed max_age.")

        configured.append((lower, upper, band))

    configured.sort(key=lambda entry: entry[0])

    for previous, current in pairwise(configured):
        if current[0] <= previous[1]:
            raise MullenScoringError(
                f"Overlapping handbook age bands for {domain}."
            )

    for lower, upper, band in configured:
        if not lower <= age <= upper:
            continue

        scores = band.get("scores")

        if not isinstance(scores, dict):
            raise MullenScoringError(
                "scores must be a raw-score dictionary."
            )

        if any(type(key) is not int or key < 0 for key in scores):
            raise MullenScoringError(
                "Raw-score lookup keys must be non-negative integers."
            )

        result = scores.get(raw_input)

        if result is None:
            raise MullenScoringError(
                f"No handbook conversion for {domain}, raw score {raw_input}, "
                f"age {age[0]} months {age[1]} days."
            )

        if not isinstance(result, dict) or any(
            field not in result or result[field] is None
            for field in SCORE_FIELDS
            if field != "age_equivalence"
        ):
            raise MullenScoringError(
                "The conversion must supply all four C1/C2 score fields."
            )

        error_widths = result["band_of_error"]

        if not isinstance(error_widths, dict) or confidence_level not in error_widths:
            raise MullenScoringError(
                "Missing band of error for the selected confidence level."
            )

        error_width = error_widths[confidence_level]

        if type(error_width) not in (int, float) or error_width <= 0:
            raise MullenScoringError(
                "Band of error must be a positive numeric width."
            )

        return {
            **{
                field: result[field]
                for field in SCORE_FIELDS
                if field != "age_equivalence"
            },
            "band_of_error": error_width,
            "age_equivalence": None,
        }

    raise MullenScoringError(
        f"No handbook age band for {domain} "
        f"at {age[0]} months {age[1]} days."
    )