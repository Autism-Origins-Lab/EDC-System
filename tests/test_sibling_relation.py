import pytest

from app.database.queries.forms import sibling_relation


@pytest.mark.parametrize(
    ("same_father", "same_mother", "expected"),
    [
        (1, 1, "Full"),
        (1, 0, "Half"),
        (0, 1, "Half"),
        (0, 0, "Not biological"),
        (None, 1, "Unknown"),
        (None, 0, "Unknown"),
        (1, None, "Unknown"),
        (0, None, "Unknown"),
        (None, None, "Unknown"),
    ],
)
def test_sibling_relation(same_father, same_mother, expected):
    assert sibling_relation(same_father, same_mother) == expected
