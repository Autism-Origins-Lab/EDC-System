SCALE_DOMAINS = (
"gross_motor",
"visual_reception",
"fine_motor",
"receptive_language",
"expressive_language",
)

C1_TABLE = (
    {
        "min_age": (0, 0),
        "max_age": (1, 30),
        "rows": {
            9: (80, 80, 80, 80, 80),
            8: (80, 80, 78, 80, 80),
            7: (73, 80, 73, 80, 80),
            6: (66, 73, 68, 80, 80),
            5: (60, 65, 63, 70, 73),
            4: (55, 58, 57, 62, 65),
            3: (48, 51, 50, 52, 55),
            2: (41, 42, 42, 43, 47),
            1: (34, 30, 35, 34, 38),
            0: (26, 22, 27, 23, 30),
        }
    },
    {
        "min_age": (2, 0),
        "max_age": (2, 30),
        "rows": {
            10: (80, 80, 80, 80, 80),
            9: (77, 80, 77, 80, 80),
            8: (69, 75, 72, 80, 80),
            7: (63, 68, 66, 78, 77),
            6: (57, 62, 60, 66, 69),
            5: (51, 55, 54, 60, 61),
            4: (44, 47, 47, 53, 54),
            3: (37, 38, 40, 44, 46),
            2: (30, 30, 33, 35, 38),
            1: (23, 21, 26, 24, 30),
            0: (20, 20, 20, 20, 21),
        },
    },
    {
        "min_age": (3, 0),
        "max_age": (3, 30),
        "rows": {
            11: (80, 80, 80, 80, 80),
            10: (76, 79, 80, 80, 80),
            9: (68, 73, 73, 80, 80),
            8: (62, 68, 67, 76, 76),
            7: (56, 62, 61, 67, 68),
            6: (50, 54, 54, 59, 62),
            5: (44, 47, 47, 51, 55),
            4: (37, 40, 40, 43, 47),
            3: (31, 33, 34, 35, 41),
            2: (24, 26, 28, 27, 33),
            1: (20, 20, 21, 20, 24),
            0: (20, 20, 20, 20, 20),
        },
    },
)

C1_BANDS_OF_ERROR = {
    "gross_motor": {90: 9, 95: 11},
    "visual_reception": {90: 8, 95: 10},
    "fine_motor": {90: 9, 95: 10},
    "receptive_language": {90: 10, 95: 12},
    "expressive_language": {90: 8, 95: 10},
}

C2_PERCENTILES = {
    80: 99, 79: 99, 78: 99, 77: 99, 76: 99, 75: 99, 74: 99,
    73: 99, 72: 99, 71: 98, 70: 98, 69: 97, 68: 96, 67: 96,
    66: 95, 65: 93, 64: 92, 63: 90, 62: 88, 61: 86,
    60: 84, 59: 82, 58: 79, 57: 76, 56: 73, 55: 69, 54: 66,
    53: 62, 52: 58, 51: 54, 50: 50, 49: 46, 48: 42, 47: 38,
    46: 34, 45: 31, 44: 27, 43: 24, 42: 21, 41: 18, 40: 16,
    39: 14, 38: 12, 37: 10, 36: 8, 35: 7, 34: 5, 33: 4,
    32: 4, 31: 3, 30: 2, 29: 2, 28: 1, 27: 1, 26: 1,
    25: 1, 24: 1, 23: 1, 22: 1, 21: 1, 20: 1,
}

C2_CATEGORIES = (
    (70, 80, "Very High"),
    (61, 69, "Above Average"),
    (40, 60, "Average"),
    (31, 39, "Below Average"),
    (20, 30, "Very Low"),
)



def _build_norms() -> dict[str, list[dict]]:
    """Expand the printed row/column layout into the service's lookup format."""
    norms = {domain: [] for domain in SCALE_DOMAINS}
    for table in C1_TABLE:
        for column, domain in enumerate(SCALE_DOMAINS):
            scores = {}
            for raw_score, row in table["rows"].items():
                t_score = row[column]
                category = next(
                    label for lower, upper, label in C2_CATEGORIES
                    if lower <= t_score <= upper
                )
                scores[raw_score] = {
                    "t_score": t_score,
                    "band_of_error": C1_BANDS_OF_ERROR[domain].copy(),
                    "percentile_rank": C2_PERCENTILES[t_score],
                    "descriptive_category": category,
                    "age_equivalence": None,
                }
            norms[domain].append({
                "min_age": table["min_age"],
                "max_age": table["max_age"],
                "scores": scores,
            })
    return norms




MULLEN_NORMS = _build_norms()
