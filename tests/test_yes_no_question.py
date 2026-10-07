import pytest
from PySide6.QtCore import Qt

from app.ui.widgets.yes_no_question import YesNoQuestion


def make_question(qtbot, **kwargs) -> YesNoQuestion:
    question = YesNoQuestion("Does your child have any siblings?", **kwargs)
    qtbot.addWidget(question)
    question.show()
    return question


def test_starts_unanswered(qtbot):
    question = make_question(qtbot)
    assert question.value() is None


def test_clicking_yes_and_no_sets_value_and_emits(qtbot):
    question = make_question(qtbot)

    with qtbot.waitSignal(question.answered) as signal:
        qtbot.mouseClick(question.yes_button, Qt.LeftButton)
    assert question.value() == 1
    assert signal.args == [1]

    with qtbot.waitSignal(question.answered) as signal:
        qtbot.mouseClick(question.no_button, Qt.LeftButton)
    assert question.value() == 0
    assert signal.args == [0]


def test_set_value_none_clears_both_buttons(qtbot):
    question = make_question(qtbot)
    question.set_value(1)
    question.set_value(None)
    assert question.value() is None
    assert not question.yes_button.isChecked()
    assert not question.no_button.isChecked()


def test_buttons_stay_exclusive_after_clearing(qtbot):
    question = make_question(qtbot)
    question.set_value(None)
    question.set_value(1)
    question.set_value(0)
    assert not question.yes_button.isChecked()
    assert question.no_button.isChecked()


@pytest.mark.parametrize("value", [1, 0, None])
def test_set_value_emits_answered(qtbot, value):
    question = make_question(qtbot)
    with qtbot.waitSignal(question.answered) as signal:
        question.set_value(value)
    assert signal.args == [value]


def test_set_value_rejects_other_values(qtbot):
    question = make_question(qtbot)
    with pytest.raises(ValueError):
        question.set_value(2)


def test_custom_answer_text_and_help(qtbot):
    question = make_question(
        qtbot,
        help_text="If yes, ask for each sibling's name and age.",
        yes_text="Yes, at least one",
        no_text="No siblings",
    )
    assert question.yes_button.text() == "Yes, at least one"
    assert question.no_button.text() == "No siblings"
    assert question.help_label.text() == "If yes, ask for each sibling's name and age."


def test_no_help_label_by_default(qtbot):
    question = make_question(qtbot)
    assert question.help_label is None
