from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit

from app.config import APP_NAME


class TopBar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(24)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")

        search = QLineEdit()
        search.setObjectName("GlobalSearch")
        search.setPlaceholderText("Search for a specific patient (Last name or Last name, Subject  ID)")
        search.setFixedWidth(420)
        search.textChanged.connect(self.filter_patients)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(search)
        

        #filtering & getting the patient.
    def filter_patients(self, search_text: str):
        self.search_working.emit()
        query = search_text.strip().lower()
        filtered_list = []
        if not query:
            return filtered_list

        for patient in self.all_patients:
            last_name = (patient.get("last_name") or "").lower()
            subject_id = str(patient.get("subject_id") or "").lower()

            if "," in query:
                parts = [p.strip() for p in query.split(",", 1)]
                name_part = parts[0]
                id_part = parts[1] if len(parts) > 1 else ""

                if name_part in last_name and id_part in subject_id:
                    filtered_list.append(patient)
            else:
                if query in last_name or query in subject_id:
                    filtered_list.append(patient)
        return filtered_list
    