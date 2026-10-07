from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Column positions, so the code says NAME instead of a bare 0
NAME, AGE, SAME_FATHER, SAME_MOTHER, ADOPTED, DIAGNOSIS = range(6)
HEADERS = ["Name", "Age", "Same bio father?", "Same bio mother?", "Adopted", "Dx"]

# What each dropdown choice saves as. Blank means unknown, which is not the same as No.
YES_NO_CHOICES = {"": None, "Yes": 1, "No": 0}


def _text(value) -> str:
    """Turn a saved value into cell text. None becomes "" and numbers become strings."""
    return "" if value is None else str(value)


def _is_blank(sibling: dict) -> bool:
    """True if the RA added a row but never filled anything in."""
    return (
        not sibling["name"]
        and not sibling["age"]
        and not sibling["diagnosis"]
        and sibling["same_bio_father"] is None
        and sibling["same_bio_mother"] is None
        and not sibling["adopted"]
    )


class SiblingsTable(QWidget):
    """One row per sibling.

    This replaces paper question 6 ("same father/mother as older sibling"):
    we ask about the father and mother for each sibling, because a child can
    have several half-siblings from different parents.
    """

    # Sent after any edit, once every row is complete (safe to call collect_siblings)
    changed = Signal()

    def __init__(self):
        super().__init__()

        self.table = QTableWidget(0, len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setMinimumHeight(180)
        # The global theme gives tables a white background, but dark mode makes
        # cell text white. Use the system palette for both so text stays readable.
        self.table.setStyleSheet(
            """
            QTableWidget {
                background: palette(base);
                color: palette(text);
                gridline-color: palette(mid);
                border: 1px solid palette(mid);
                border-radius: 6px;
                /* The global theme's pale-blue selection hides white text in dark
                   mode, so use a see-through tint of the app's blue instead */
                selection-background-color: rgba(29, 99, 237, 0.35);
                selection-color: palette(text);
            }
            QTableWidget:disabled { color: #6b7280; }
            QHeaderView::section {
                background: palette(window);
                color: palette(window-text);
                border: 0;
                border-bottom: 1px solid palette(mid);
                font-weight: 600;
                padding: 8px;
            }
            """
        )
        # cellChanged sends (row, column), which changed() doesn't take, so drop them
        self.table.cellChanged.connect(lambda *_args: self.changed.emit())
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(DIAGNOSIS, QHeaderView.Stretch)

        self.add_button = QPushButton("+ Add sibling")
        self.add_button.setObjectName("SecondaryButton")
        self.add_button.setCursor(Qt.PointingHandCursor)
        # clicked sends a True/False argument we don't want, so wrap the call
        self.add_button.clicked.connect(lambda: self.add_sibling())

        self.remove_button = QPushButton("Remove selected sibling")
        self.remove_button.setObjectName("SecondaryButton")
        self.remove_button.setCursor(Qt.PointingHandCursor)
        self.remove_button.clicked.connect(self.remove_selected_sibling)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.add_button)
        buttons_row.addWidget(self.remove_button)
        buttons_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(buttons_row)

    # --- Adding and removing rows ---

    def add_sibling(self, sibling: dict | None = None) -> None:
        sibling = sibling or {}

        # Mute the table while the row is half-built, so nothing reads a row
        # that is still missing cells. Announce one change at the end instead.
        self.table.blockSignals(True)
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, NAME, QTableWidgetItem(_text(sibling.get("name"))))
        self.table.setItem(row, AGE, QTableWidgetItem(_text(sibling.get("age"))))
        self.table.setItem(row, DIAGNOSIS, QTableWidgetItem(_text(sibling.get("diagnosis"))))

        for column, key in ((SAME_FATHER, "same_bio_father"), (SAME_MOTHER, "same_bio_mother")):
            combo = self._yes_no_combo(sibling.get(key))
            combo.currentIndexChanged.connect(lambda *_args: self.changed.emit())
            self.table.setCellWidget(row, column, combo)

        adopted_item = QTableWidgetItem()
        adopted_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        adopted_item.setCheckState(Qt.Checked if sibling.get("adopted") else Qt.Unchecked)
        self.table.setItem(row, ADOPTED, adopted_item)
        self.table.blockSignals(False)

        self.changed.emit()

    def remove_selected_sibling(self) -> None:
        row = self.table.currentRow()
        if row != -1:  # -1 means no row is selected
            self.table.removeRow(row)
            self.changed.emit()

    @staticmethod
    def _yes_no_combo(value: int | None) -> QComboBox:
        combo = QComboBox()
        combo.addItems(list(YES_NO_CHOICES))
        for text, choice_value in YES_NO_CHOICES.items():
            if choice_value == value:
                combo.setCurrentText(text)
        return combo

    # --- Reading and writing all rows ---

    def collect_siblings(self) -> list[dict]:
        siblings = []
        for row in range(self.table.rowCount()):
            sibling = {
                "name": self.table.item(row, NAME).text().strip(),
                "age": self.table.item(row, AGE).text().strip(),
                "same_bio_father": YES_NO_CHOICES[self.table.cellWidget(row, SAME_FATHER).currentText()],
                "same_bio_mother": YES_NO_CHOICES[self.table.cellWidget(row, SAME_MOTHER).currentText()],
                "adopted": int(self.table.item(row, ADOPTED).checkState() == Qt.Checked),
                "diagnosis": self.table.item(row, DIAGNOSIS).text().strip(),
            }
            if not _is_blank(sibling):
                siblings.append(sibling)
        return siblings

    def set_siblings(self, siblings: list[dict]) -> None:
        self.table.setRowCount(0)
        for sibling in siblings:
            self.add_sibling(sibling)
        self.changed.emit()
