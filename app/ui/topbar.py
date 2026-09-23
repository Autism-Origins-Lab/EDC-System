from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Signal

from app.config import APP_NAME

class TopBar(QFrame):
    menu_clicked = Signal()
    search_working = Signal()
    patients_filtered = Signal(list)
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(58)
        self.all_patients: list[dict] = [] #a place to store all the patients in a list. makes it easier to return & navigate

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(24)

        menu_button = QPushButton(chr(9776))
        menu_button.setObjectName("BurgerMenu")
        menu_button.setFixedSize(38,38)
        menu_button.clicked.connect(self.menu_clicked.emit)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")

        search = QLineEdit()
        search.setObjectName("GlobalSearch")
        search.setPlaceholderText("Search for a specific patient (Child name or Child name, Subject  ID)")
        search.setFixedWidth(420)
        search.textChanged.connect(self.filter_patients)

        layout.addWidget(menu_button)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(search)

        #populate & update patient list to load 
    def set_patients(self, patients: list[dict]) -> None:
        self.all_patients = patients

        #filtering & getting the patient.
    def filter_patients(self, search_text: str) -> None:
        self.search_working.emit()
        query = search_text.strip().lower()

        if not query:
            self.patients_filtered.emit(self.all_patients)
            return

        filtered_list = []

        for patient in self.all_patients:
            child_name = str(patient.get("child_name") or "").lower()
            subject_id = str(patient.get("subject_id") or "").lower()

            if "," in query:
                parts = [p.strip() for p in query.split(",", 1)]
                name_part = parts[0]
                id_part = parts[1] if len(parts) > 1 else ""

                if name_part in child_name and id_part in subject_id:
                    filtered_list.append(patient)
            else:
                if query in child_name or query in subject_id:
                    filtered_list.append(patient)

        self.patients_filtered.emit(filtered_list) #I want this list to be sent to patients_view to displau the table as needed, when something is searched 
    
