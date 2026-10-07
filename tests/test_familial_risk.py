import pytest
from PySide6.QtCore import Qt

import app.ui.views.family_medical_history_view as view_module
from app.database.queries.forms import HIGH_RISK, LOW_RISK, familial_risk

NO_SIBLINGS = {"family_psychiatric": 0, "has_siblings": 0}
SIBLINGS_NO_DX = {"family_psychiatric": 0, "has_siblings": 1, "sibling_autism": 0, "sibling_adhd": 0}


@pytest.mark.parametrize(
    ("answers", "siblings", "expected"),
    [
        # High: a sibling with ASD, whatever else is true
        ({"has_siblings": 1, "sibling_autism": 1}, [], HIGH_RISK),
        ({**SIBLINGS_NO_DX, "sibling_autism": 1, "family_psychiatric": 1}, [], HIGH_RISK),
        # Low: no diagnosis anywhere, with or without siblings
        (NO_SIBLINGS, [], LOW_RISK),
        (SIBLINGS_NO_DX, [{"name": "Maya", "diagnosis": ""}], LOW_RISK),
        # Not determined: some other diagnosis in the family
        ({**NO_SIBLINGS, "family_psychiatric": 1}, [], None),
        ({**SIBLINGS_NO_DX, "sibling_adhd": 1}, [], None),
        (SIBLINGS_NO_DX, [{"name": "Maya", "diagnosis": "Anxiety"}], None),
        # Not determined: questions still unanswered
        ({}, [], None),
        ({"family_psychiatric": 0}, [], None),
        ({"family_psychiatric": 0, "has_siblings": 1, "sibling_autism": 0}, [], None),
    ],
)
def test_familial_risk(answers, siblings, expected):
    risk, reason = familial_risk(answers, siblings)
    assert risk == expected
    assert reason


def make_view(qtbot, monkeypatch) -> view_module.FamilyMedicalHistoryView:
    monkeypatch.setattr(view_module, "get_family_medical_history", lambda _patient_id: None)
    monkeypatch.setattr(view_module, "list_siblings", lambda _patient_id: [])
    view = view_module.FamilyMedicalHistoryView(patient_id=1)
    qtbot.addWidget(view)
    view.show()
    return view


def test_suggestion_updates_as_answers_change(qtbot, monkeypatch):
    view = make_view(qtbot, monkeypatch)
    assert "not determined" in view.risk_suggestion.text()

    qtbot.mouseClick(view.family_psychiatric_question.no_button, Qt.LeftButton)
    qtbot.mouseClick(view.has_siblings_question.no_button, Qt.LeftButton)
    assert "Low" in view.risk_suggestion.text()

    qtbot.mouseClick(view.has_siblings_question.yes_button, Qt.LeftButton)
    qtbot.mouseClick(view.sibling_autism_section.question.yes_button, Qt.LeftButton)
    assert "High" in view.risk_suggestion.text()


def test_suggestion_hidden_when_ineligible(qtbot, monkeypatch):
    view = make_view(qtbot, monkeypatch)
    assert view.risk_suggestion.isVisible()
    qtbot.mouseClick(view.disqualifier_questions["parent_autism"].yes_button, Qt.LeftButton)
    assert not view.risk_suggestion.isVisible()


def test_loading_saved_siblings_feeds_the_suggestion(qtbot, monkeypatch):
    monkeypatch.setattr(
        view_module,
        "get_family_medical_history",
        lambda _patient_id: {
            "family_psychiatric": 0, "has_siblings": 1, "sibling_autism": 0, "sibling_adhd": 0,
        },
    )
    monkeypatch.setattr(
        view_module, "list_siblings", lambda _patient_id: [{"name": "Leo", "diagnosis": "Anxiety"}]
    )
    view = view_module.FamilyMedicalHistoryView(patient_id=1)
    qtbot.addWidget(view)
    assert "not determined" in view.risk_suggestion.text()

    # Clearing the sibling's diagnosis leaves no diagnosis anywhere, so Low
    view.siblings_table.table.item(0, 5).setText("")
    assert "Low" in view.risk_suggestion.text()


def test_table_announces_changes_only_when_rows_are_complete(qtbot):
    from app.ui.widgets.siblings_table import SiblingsTable

    siblings_table = SiblingsTable()
    qtbot.addWidget(siblings_table)
    seen = []
    siblings_table.changed.connect(lambda: seen.append(siblings_table.collect_siblings()))
    siblings_table.add_sibling({"name": "Maya", "age": "4"})
    siblings_table.remove_selected_sibling()  # nothing selected, no change
    assert seen == [[{"name": "Maya", "age": "4", "same_bio_father": None,
                      "same_bio_mother": None, "adopted": 0, "diagnosis": ""}]]
