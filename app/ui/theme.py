APP_STYLESHEET = """
QMainWindow {
    background: #ffffff;
    color: #1f2937;
    font-family: "Segoe UI";
    font-size: 13px;
}

QFrame#TopBar {
    background: #1d63ed;
}

QLabel#AppTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 600;
}

QLineEdit#GlobalSearch {
    background: rgba(255, 255, 255, 0.18);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 6px;
    padding: 8px 12px;
}

QLineEdit#GlobalSearch::placeholder {
    color: rgba(255, 255, 255, 0.72);
}

QFrame#Sidebar {
    background: #f6f7f9;
    border-right: 1px solid #e5e7eb;
}

QPushButton[nav="true"] {
    background: transparent;
    border: 0;
    border-radius: 6px;
    color: #1f2937;
    font-weight: 500;
    padding: 10px 14px;
    text-align: left;
}

QPushButton[active="true"] {
    background: #eaf1ff;
    color: #1d63ed;
}

QPushButton#PrimaryButton {
    background: #1d63ed;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    font-weight: 600;
    padding: 9px 14px;
}

QPushButton#SecondaryButton {
    background: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-weight: 500;
    padding: 8px 12px;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    gridline-color: #eef0f3;
    selection-background-color: #eaf1ff;
    selection-color: #111827;
}

QHeaderView::section {
    background: #ffffff;
    border: 0;
    border-bottom: 1px solid #e5e7eb;
    color: #374151;
    font-weight: 600;
    padding: 10px;
}

QLabel#PageTitle {
    color: #111827;
    font-size: 24px;
    font-weight: 650;
}

QLabel#MetricValue {
    color: #0f9f6e;
    font-size: 20px;
    font-weight: 600;
}

QLabel#Muted {
    color: #6b7280;
}
"""
