from PySide6.QtCore import Qt

from app.ui.widgets.conditional_section import ConditionalSection


def make_section(qtbot) -> ConditionalSection:
    section = ConditionalSection(
        key="parent_diagnosed",
        label="Mother or father has been diagnosed",
        options={"parent_autism": "Autism"},
        other_key="parent_other",
    )
    qtbot.addWidget(section)
    section.show()
    return section


def click_yes(qtbot, section: ConditionalSection) -> None:
    qtbot.mouseClick(section.question.yes_button, Qt.LeftButton)


def click_no(qtbot, section: ConditionalSection) -> None:
    qtbot.mouseClick(section.question.no_button, Qt.LeftButton)


def test_panel_shows_only_on_yes(qtbot):
    section = make_section(qtbot)
    assert not section.panel.isVisible()
    click_yes(qtbot, section)
    assert section.panel.isVisible()
    click_no(qtbot, section)
    assert not section.panel.isVisible()


def test_unanswered_saves_none_not_zero(qtbot):
    section = make_section(qtbot)
    assert section.get_data()["parent_diagnosed"] is None


def test_yes_and_no_save_one_and_zero(qtbot):
    section = make_section(qtbot)
    click_yes(qtbot, section)
    assert section.get_data()["parent_diagnosed"] == 1
    click_no(qtbot, section)
    assert section.get_data()["parent_diagnosed"] == 0


def test_answering_no_blanks_hidden_answers(qtbot):
    section = make_section(qtbot)
    click_yes(qtbot, section)
    section.option_checkboxes["parent_autism"].setChecked(True)
    click_no(qtbot, section)
    assert section.get_data()["parent_autism"] == 0


def test_set_data_restores_answer_and_shows_panel(qtbot):
    section = make_section(qtbot)
    section.set_data({"parent_diagnosed": 1, "parent_autism": 1})
    assert section.question.value() == 1
    assert section.panel.isVisible()
    assert section.option_checkboxes["parent_autism"].isChecked()


def test_set_data_none_clears_answer_and_hides_panel(qtbot):
    section = make_section(qtbot)
    click_yes(qtbot, section)
    section.set_data({"parent_diagnosed": None})
    assert section.question.value() is None
    assert not section.panel.isVisible()


def test_yes_with_nothing_underneath_is_an_error(qtbot):
    section = make_section(qtbot)
    click_yes(qtbot, section)
    assert len(section.validation_errors()) == 1
    click_no(qtbot, section)
    assert section.validation_errors() == []


def test_other_requires_text(qtbot):
    section = make_section(qtbot)
    click_yes(qtbot, section)
    section.other_checkbox.setChecked(True)
    assert len(section.validation_errors()) == 1
    section.other_input.setText("Bipolar disorder")
    assert section.validation_errors() == []
