from PySide6.QtCore import Qt

from app.ui.widgets.siblings_table import (
    ADOPTED,
    AGE,
    DIAGNOSIS,
    NAME,
    SAME_FATHER,
    SAME_MOTHER,
    SiblingsTable,
)


def make_table(qtbot) -> SiblingsTable:
    siblings_table = SiblingsTable()
    qtbot.addWidget(siblings_table)
    siblings_table.show()
    return siblings_table


def test_add_button_adds_a_row(qtbot):
    siblings_table = make_table(qtbot)
    qtbot.mouseClick(siblings_table.add_button, Qt.LeftButton)
    qtbot.mouseClick(siblings_table.add_button, Qt.LeftButton)
    assert siblings_table.table.rowCount() == 2


def test_collect_reads_every_column(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling()
    table = siblings_table.table
    table.item(0, NAME).setText(" Maya ")
    table.item(0, AGE).setText("4")
    table.cellWidget(0, SAME_FATHER).setCurrentText("Yes")
    table.cellWidget(0, SAME_MOTHER).setCurrentText("No")
    table.item(0, ADOPTED).setCheckState(Qt.Checked)
    table.item(0, DIAGNOSIS).setText("ADHD")

    assert siblings_table.collect_siblings() == [
        {
            "name": "Maya",
            "age": "4",
            "same_bio_father": 1,
            "same_bio_mother": 0,
            "adopted": 1,
            "diagnosis": "ADHD",
        }
    ]


def test_blank_dropdown_means_unknown_not_no(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling({"name": "Leo"})
    sibling = siblings_table.collect_siblings()[0]
    assert sibling["same_bio_father"] is None
    assert sibling["same_bio_mother"] is None


def test_blank_rows_are_skipped(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling()
    siblings_table.add_sibling({"name": "Leo"})
    siblings_table.add_sibling()
    assert [sibling["name"] for sibling in siblings_table.collect_siblings()] == ["Leo"]


def test_row_with_only_a_no_answer_is_kept(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling({"same_bio_father": 0})
    assert len(siblings_table.collect_siblings()) == 1


def test_set_siblings_round_trip(qtbot):
    siblings = [
        {"name": "Maya", "age": "4", "same_bio_father": 1, "same_bio_mother": 1,
         "adopted": 0, "diagnosis": ""},
        {"name": "Leo", "age": "9", "same_bio_father": 0, "same_bio_mother": None,
         "adopted": 1, "diagnosis": "ASD"},
    ]
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling({"name": "old row, should be replaced"})
    siblings_table.set_siblings(siblings)
    assert siblings_table.collect_siblings() == siblings


def test_number_age_from_database_shows_as_text(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.add_sibling({"name": "Maya", "age": 4})
    assert siblings_table.table.item(0, AGE).text() == "4"


def test_remove_selected_sibling(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.set_siblings([{"name": "Maya"}, {"name": "Leo"}])
    siblings_table.table.selectRow(0)
    qtbot.mouseClick(siblings_table.remove_button, Qt.LeftButton)
    assert [sibling["name"] for sibling in siblings_table.collect_siblings()] == ["Leo"]


def test_remove_with_nothing_selected_does_nothing(qtbot):
    siblings_table = make_table(qtbot)
    siblings_table.set_siblings([{"name": "Maya"}])
    siblings_table.table.setCurrentCell(-1, -1)
    siblings_table.remove_selected_sibling()
    assert siblings_table.table.rowCount() == 1
