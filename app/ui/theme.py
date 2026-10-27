"""Frontend themes, grouped and labeled by component.

APP_STYLESHEET supplies the shared application theme. Component-specific
stylesheets are imported by their widgets and applied locally to preserve
Qt stylesheet precedence and support standalone views. Layout and behavior
remain in the components; colors, fonts, and QSS definitions live here.
"""

from PySide6.QtGui import QFont

# Scoped to the patient workspace so dashboard and top-bar styling stay independent.
PATIENT_WORKSPACE_STYLESHEET = """
QDialog#PatientWorkspace, QDialog#PatientWorkspace QWidget {
    background-color: #ffffff;
    color: #1f2937;
    font-family: "Segoe UI";
    font-size: 13px;
}
QDialog#PatientWorkspace QLabel {
    background: transparent;
    color: #1f2937;
}
QDialog#PatientWorkspace QLabel#WorkspaceTitle {
    font-size: 28px;
    font-weight: 600;
}
QDialog#PatientWorkspace QLabel#WorkspaceMuted {
    color: #6b7280;
}
QDialog#PatientWorkspace QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 9px;
    margin-top: 16px;
}
QDialog#PatientWorkspace QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 22px;
    padding: 0 4px;
    color: #6b7280;
}
QDialog#PatientWorkspace QGroupBox QWidget {
    background-color: transparent;
}
QDialog#PatientWorkspace QFrame#FormStep,
QDialog#PatientWorkspace QWidget#FormStepTrack {
    background: transparent;
    border: 0;
}
QDialog#PatientWorkspace QLabel#FormStepTitle {
    background: transparent;
    color: #6b7280;
}
QDialog#PatientWorkspace QLabel#FormStepNumber {
    background-color: #ffffff;
    color: #6b7280;
    border: 2px solid #dfe4e1;
    border-radius: 22px;
    font-size: 20px;
    font-weight: 600;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="saved"] QLabel#FormStepNumber {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #1b7652, stop: 1 #258046);
    color: #ffffff;
    border-color: #218057;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="current"] QLabel#FormStepNumber {
    color: #1c7c54;
    border: 3px solid #27865c;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="saved"] QLabel#FormStepTitle,
QDialog#PatientWorkspace QFrame#FormStep[stepState="current"] QLabel#FormStepTitle {
    color: #1c7c54;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="current"] QLabel#FormStepTitle {
    font-weight: 600;
}
QDialog#PatientWorkspace QFrame#FormConnector {
    background-color: #dfe4e1;
    border: 0;
}
QDialog#PatientWorkspace QFrame#FormConnector[filled="true"] {
    background-color: #27865c;
}
QDialog#PatientWorkspace QFrame#FormConnector[edge="true"] {
    background: transparent;
}
QDialog#PatientWorkspace QLineEdit,
QDialog#PatientWorkspace QComboBox,
QDialog#PatientWorkspace QTextEdit {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
    selection-background-color: #eaf1ff;
    selection-color: #1f2937;
}
QDialog#PatientWorkspace QLineEdit:focus,
QDialog#PatientWorkspace QComboBox:focus,
QDialog#PatientWorkspace QTextEdit:focus {
    border-color: #166AB8;
}
QDialog#PatientWorkspace QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1f2937;
    selection-background-color: #eaf1ff;
}
QDialog#PatientWorkspace QCheckBox {
    color: #1f2937;
    background: transparent;
    spacing: 10px;
}
QDialog#PatientWorkspace QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #9ca3af;
    border-radius: 2px;
    background-color: #ffffff;
}
QDialog#PatientWorkspace QCheckBox::indicator:checked {
    background-color: #166AB8;
    border-color: #166AB8;
}
QDialog#PatientWorkspace QCheckBox::indicator:hover {
    border-color: #166AB8;
}
QDialog#PatientWorkspace QScrollArea {
    border: 0;
    background: transparent;
}
QDialog#PatientWorkspace QPushButton {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 10px 16px;
}
QDialog#PatientWorkspace QPushButton#WorkspaceSave {
    background-color: #166AB8;
    color: #ffffff;
    border-color: #166AB8;
    font-weight: 600;
}
QDialog#PatientWorkspace QPushButton#WorkspaceSave:hover {
    background-color: #115492;
}
QDialog#PatientWorkspace QPushButton#WorkspaceBack:hover {
    background-color: #eaf1ff;
}
QDialog#PatientWorkspace QPushButton:disabled,
QDialog#PatientWorkspace QPushButton#WorkspaceSave:disabled {
    background-color: #f6f7f9;
    color: #6b7280;
    border-color: #e5e7eb;
}
QDialog#PatientWorkspace QPushButton:focus {
    border: 2px solid #166AB8;
}
QDialog#PatientWorkspace QPushButton#WorkspaceDelete {
    color: #b42318;
    border-color: #f2b8b5;
}
QDialog#PatientWorkspace QPushButton#WorkspaceDelete:hover {
    background-color: #fff1f0;
}
QDialog#PatientWorkspace QTableWidget,
QDialog#PatientWorkspace QTreeWidget#SummaryAnswers {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    gridline-color: #EDF2F7;
}
QDialog#PatientWorkspace QTreeWidget#SummaryAnswers::item {
    padding: 6px;
}
QDialog#PatientWorkspace QTreeWidget#SummaryAnswers::item:selected {
    background-color: #eaf1ff;
    color: #1f2937;
}
QDialog#PatientWorkspace QHeaderView::section {
    background-color: #115492;
    color: #FCFCFD;
    border: 0;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px;
}
"""

# Scoped to the patient creation dialog and aligned with the patient workspace.
NEW_PATIENT_DIALOG_STYLESHEET = """
QDialog#NewPatientDialog {
    background-color: #ffffff;
    color: #1f2937;
    font-family: "Segoe UI";
    font-size: 13px;
}
QDialog#NewPatientDialog QLabel {
    background: transparent;
    color: #1f2937;
}
QDialog#NewPatientDialog QLabel#NewPatientTitle {
    color: #172f52;
    font-size: 26px;
    font-weight: 600;
}
QDialog#NewPatientDialog QLabel#NewPatientSubtitle {
    color: #6b7280;
}
QDialog#NewPatientDialog QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 9px;
    margin-top: 16px;
}
QDialog#NewPatientDialog QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 18px;
    padding: 0 5px;
    color: #6b7280;
}
QDialog#NewPatientDialog QLineEdit#NewPatientSubjectId {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #d7e0ec;
    border-radius: 6px;
    padding: 9px 12px;
    min-height: 20px;
    selection-background-color: #eaf1ff;
    selection-color: #1f2937;
    placeholder-text-color: #9ca3af;
}
QDialog#NewPatientDialog QLineEdit#NewPatientSubjectId:hover {
    border-color: #b8c6d9;
}
QDialog#NewPatientDialog QLineEdit#NewPatientSubjectId:focus {
    border-color: #166AB8;
}
QDialog#NewPatientDialog QPushButton {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #d7e0ec;
    border-radius: 6px;
    min-width: 96px;
    padding: 10px 18px;
}
QDialog#NewPatientDialog QPushButton#NewPatientCancel:hover {
    background-color: #f1f5f9;
}
QDialog#NewPatientDialog QPushButton#NewPatientCreate {
    background-color: #166AB8;
    color: #ffffff;
    border-color: #166AB8;
    font-weight: 600;
}
QDialog#NewPatientDialog QPushButton#NewPatientCreate:hover {
    background-color: #115492;
    border-color: #115492;
}
QDialog#NewPatientDialog QPushButton#NewPatientCreate:pressed {
    background-color: #0d4478;
    border-color: #0d4478;
}
"""

# Shared application theme: main window, navigation, labels, buttons, and forms.
APP_STYLESHEET = """
/* Application / main window */
QMainWindow {
    background: #ffffff;
    color: #1f2937;
    font-family: "Segoe UI";
    font-size: 13px;
}

/* Shared form labels (all form views and dialogs) */
QLabel{
    color: #1f2937;
}

/* Patient detail / tabs */
QTabs{
    alignment: center;
}
/* Top bar / container */
QFrame#TopBar {
    background: #1d63ed;
}

/* Top bar / application title */
QLabel#AppTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 600;
}

/* Top bar / global search */
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

/* Sidebar / container */
QFrame#Sidebar {
    background: #f6f7f9;
    border-right: 1px solid #e5e7eb;
}

/* Sidebar / navigation buttons */
QPushButton[nav="true"] {
    background: transparent;
    border: 0;
    border-radius: 6px;
    color: #1f2937;
    font-weight: 500;
    padding: 10px 14px;
    text-align: left;
}

/* Sidebar / active navigation button */
QPushButton[active="true"] {
    background: #eaf1ff;
    color: #1d63ed;
}

/* Shared primary buttons (form save buttons and new patient) */
QPushButton#PrimaryButton {
    background: #1d63ed;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    font-weight: 600;
    padding: 9px 14px;
}

/* Shared secondary buttons (patient sort, filters, export) */
QPushButton#SecondaryButton {
    background: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-weight: 500;
    padding: 8px 12px;
}

/* Settings / preferences card */
QFrame#SettingsCard{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
}

/* Shared form combo boxes / hover */
QComboBox:hover{
    border-color: #1d63ed;
}

/* Top bar / menu button */
QPushButton#MenuButton {
    background: transparent;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    font-size: 22px;
    font-weight: 600;
}

QPushButton#MenuButton:hover {
    background: rgba(255, 255, 255, 0.16);
}

/* Shared form checkboxes */
QCheckBox {
    color: #1f2937;
    spacing: 8px;
}

/* Shared tables / body */
QTableWidget {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    gridline-color: #eef0f3;
    selection-background-color: #eaf1ff;
    selection-color: #111827;
}

/* Shared tables / header */
QHeaderView::section {
    background: #ffffff;
    border: 0;
    border-bottom: 1px solid #e5e7eb;
    color: #374151;
    font-weight: 600;
    padding: 10px;
}

/* Shared page titles (patients, settings, placeholders, Mullen) */
QLabel#PageTitle {
    color: #111827;
    font-size: 24px;
    font-weight: 650;
}

/* Shared metric values */
QLabel#MetricValue {
    color: #0f9f6e;
    font-size: 20px;
    font-weight: 600;
}

/* Shared page subtitles and placeholder messages */
QLabel#Muted {
    color: #6b7280;
}
"""


# TopBar: container override and rounded search field.
TOPBAR_STYLESHEET = "QFrame#TopBar { background-color: #166AB8; }"
TOPBAR_SEARCH_STYLESHEET = "border-radius: 9999px;"


# PatientsView: status palette used by the donut chart and legend.
PATIENTS_PENDING_COLOR = "#D00B60"
PATIENTS_READY_COLOR = "#08AEA9"
PATIENTS_EDGE_COLOR = "#5C5C5C"

# DonutChart: track and center text.
DONUT_TRACK_COLOR = "#1a1a1a"
DONUT_CENTER_COLOR = "#1a1a1a"
DONUT_CENTER_FONT_POINT_SIZE = 14
DONUT_CENTER_FONT_WEIGHT = QFont.Weight.Bold

# PatientsView: new patient button.
PATIENTS_NEW_PATIENT_BUTTON_STYLESHEET = """
QPushButton {
    background-color: #166AB8;
    color: #FFFFFF;
    border-radius: 20px;
    padding: 12px 16px;
}
QPushButton:hover {
    background-color: #115492;
}
QPushButton:pressed {
    background-color: #115492;
}
"""

# PatientsView: eligibility filter buttons.
PATIENTS_FILTER_BUTTON_STYLESHEET = """
QPushButton:hover {
    background-color: #F1F5F9;
}
QPushButton:pressed {
    background-color: #F1F5F9;
}
"""

# PatientsView: donut caption, eligibility label, and legend labels.
PATIENTS_DONUT_CAPTION_STYLESHEET = "color: #666666; font-size: 11px; font-weight: bold;"
PATIENTS_ELIGIBILITY_LABEL_STYLESHEET = "font-weight: bold; color: #120713;"
PATIENTS_LEGEND_TEXT_STYLESHEET = "color: #1a1a1a; font-size: 13px;"


def patients_legend_dot_stylesheet(color: str) -> str:
    """PatientsView: rounded legend marker in the supplied status color."""
    return f"background-color: {color}; border-radius: 6px;"


# PatientsView: table body, item states, header, and vertical scrollbar.
PATIENTS_TABLE_ITEM_COLOR = "#000000"
PATIENTS_TABLE_STYLESHEET = """
QTableWidget { /*Items in the table */
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #EDF2F7;
    font-size: 13px;
    color: #1A202C;
    outline: none;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #EDF2F7;
}

QTableWidget::item:hover {
    background-color: #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #913899;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #115492;
    color: #FCFCFD;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    border-right: 1px solid #EDF2F7;
}

QHeaderView::section:last {
    border-right: none;
}

QScrollBar:vertical {
    border: none;
    background: #F7FAFC;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E0;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #A0AEC0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


# PatientDetailView: completion button states.

def _patient_completion_button_stylesheet(color: str) -> str:
    return f"""
QPushButton {{
    background-color: {color};
    color: #FFFFFF;
    border-radius: 20px;
    padding: 12px 16px;
}}
"""


PATIENT_DETAIL_COMPLETION_DISABLED_STYLESHEET = _patient_completion_button_stylesheet("#696969")
PATIENT_DETAIL_UNMARK_COMPLETE_STYLESHEET = _patient_completion_button_stylesheet("#D82454")
PATIENT_DETAIL_MARK_COMPLETE_STYLESHEET = _patient_completion_button_stylesheet("#44CCAA")


# SettingsView: option labels, checkboxes, combo boxes, and popup lists.
SETTINGS_STYLESHEET = """
QWidget#SettingsView QWidget#SettingsContent {
    background-color: #f8fafc;
}
QWidget#SettingsView QLabel { color: #1f2937; }
QWidget#SettingsView QLabel#BackupTitle { font-size: 15px; font-weight: 600; }
QWidget#SettingsView QLabel#SettingsOptionLabel,
QWidget#SettingsView QCheckBox#SettingsOptionCheckBox {
    color: #1f2937;
}

QWidget#SettingsView QComboBox {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 7px 32px 7px 10px;
}

QWidget#SettingsView QComboBox:hover,
QWidget#SettingsView QComboBox:focus {
    border-color: #1d63ed;
}

QWidget#SettingsView QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    background-color: transparent;
    border: none;
}

QWidget#SettingsView QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
}

QWidget#SettingsView QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #111827;
    selection-background-color: #eaf1ff;
    selection-color: #1d63ed;
    border: 1px solid #d1d5db;
}
"""

# SettingsComboBox: custom dropdown chevron.
SETTINGS_ARROW_COLOR = "#9ca3af"
SETTINGS_DISABLED_ARROW_COLOR = "#d1d5db"
SETTINGS_ARROW_STROKE_WIDTH = 1.5


DARK_APP_STYLESHEET = """
QMainWindow,
QWidget#ApplicationRoot,
QFrame#ApplicationBody,
QStackedWidget#ApplicationPages,
QWidget#PatientsView,
QWidget#SettingsView,
QWidget#PlaceholderPage {
    background-color: #111827;
    color: #e5e7eb;
}
QLabel, QCheckBox, QLabel#PageTitle, QLabel#MetricValue {
    color: #e5e7eb;
}
QLabel#Muted { color: #9ca3af; }
QFrame#TopBar { background-color: #164f8a; }
QFrame#Sidebar {
    background-color: #182235;
    border-right-color: #374151;
}
QPushButton[nav="true"] { color: #e5e7eb; }
QPushButton[active="true"] {
    background-color: #243b5d;
    color: #93c5fd;
}
QPushButton#SecondaryButton {
    background-color: #1f2937;
    color: #e5e7eb;
    border-color: #4b5563;
}
QFrame#SettingsCard {
    background-color: #182235;
    border-color: #374151;
}
QMessageBox { background-color: #182235; }
QMessageBox QLabel { color: #e5e7eb; }
"""

DARK_SETTINGS_STYLESHEET = """
QWidget#SettingsView QWidget#SettingsContent {
    background-color: #111827;
}
QWidget#SettingsView QLabel { color: #e5e7eb; }
QWidget#SettingsView QLabel#SettingsOptionLabel,
QWidget#SettingsView QCheckBox#SettingsOptionCheckBox {
    color: #e5e7eb;
}
QWidget#SettingsView QComboBox,
QWidget#SettingsView QComboBox QAbstractItemView {
    background-color: #1f2937;
    color: #f3f4f6;
    border-color: #4b5563;
}
"""

DARK_PATIENTS_TABLE_STYLESHEET = """
QTableWidget {
    background-color: #182235;
    color: #e5e7eb;
    border-color: #374151;
    gridline-color: #374151;
}
QTableWidget::item { border-bottom-color: #374151; }
QTableWidget::item:hover { background-color: #243b5d; }
QHeaderView::section {
    background-color: #1f2937;
    color: #e5e7eb;
    border-bottom-color: #4b5563;
}
"""

DARK_PATIENT_WORKSPACE_STYLESHEET = """
QDialog#PatientWorkspace, QDialog#PatientWorkspace QWidget {
    background-color: #111827;
    color: #e5e7eb;
}
QDialog#PatientWorkspace QLabel { color: #e5e7eb; }
QDialog#PatientWorkspace QLabel#WorkspaceMuted,
QDialog#PatientWorkspace QGroupBox::title { color: #9ca3af; }
QDialog#PatientWorkspace QGroupBox,
QDialog#PatientWorkspace QLineEdit,
QDialog#PatientWorkspace QComboBox,
QDialog#PatientWorkspace QTextEdit,
QDialog#PatientWorkspace QPushButton,
QDialog#PatientWorkspace QTableWidget,
QDialog#PatientWorkspace QTreeWidget#SummaryAnswers {
    background-color: #1f2937;
    color: #e5e7eb;
    border-color: #4b5563;
}
QDialog#PatientWorkspace QLabel#FormStepTitle {
    color: #9ca3af;
}
QDialog#PatientWorkspace QLabel#FormStepNumber {
    background-color: #111827;
    color: #9ca3af;
    border-color: #4b5563;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="current"] QLabel#FormStepNumber {
    background-color: #111827;
    color: #6fdaa6;
    border-color: #6fdaa6;
}
QDialog#PatientWorkspace QFrame#FormStep[stepState="saved"] QLabel#FormStepTitle,
QDialog#PatientWorkspace QFrame#FormStep[stepState="current"] QLabel#FormStepTitle {
    color: #6fdaa6;
}
QDialog#PatientWorkspace QFrame#FormConnector {
    background-color: #4b5563;
}
QDialog#PatientWorkspace QFrame#FormConnector[filled="true"] {
    background-color: #6fdaa6;
}
QDialog#PatientWorkspace QFrame#FormConnector[edge="true"] {
    background: transparent;
}
QDialog#PatientWorkspace QPushButton:disabled,
QDialog#PatientWorkspace QPushButton#WorkspaceSave:disabled {
    background-color: #182235;
    color: #9ca3af;
    border-color: #374151;
}
QDialog#PatientWorkspace QPushButton#WorkspaceDelete {
    color: #fca5a5;
    border-color: #fca5a5;
}
QDialog#PatientWorkspace QPushButton#WorkspaceDelete:hover {
    background-color: #3b2029;
}
QDialog#PatientWorkspace QTreeWidget#SummaryAnswers::item:selected {
    background-color: #243b5d;
    color: #e5e7eb;
}
QDialog#PatientWorkspace QComboBox QAbstractItemView,
QDialog#PatientWorkspace QHeaderView::section {
    background-color: #1f2937;
    color: #e5e7eb;
}
"""

DARK_NEW_PATIENT_DIALOG_STYLESHEET = """
QDialog#NewPatientDialog, QDialog#NewPatientDialog QGroupBox {
    background-color: #111827;
    color: #e5e7eb;
    border-color: #374151;
}
QDialog#NewPatientDialog QLabel,
QDialog#NewPatientDialog QLabel#NewPatientTitle { color: #e5e7eb; }
QDialog#NewPatientDialog QLabel#NewPatientSubtitle,
QDialog#NewPatientDialog QGroupBox::title { color: #9ca3af; }
QDialog#NewPatientDialog QLineEdit#NewPatientSubjectId,
QDialog#NewPatientDialog QPushButton {
    background-color: #1f2937;
    color: #e5e7eb;
    border-color: #4b5563;
}
"""

DARK_MULLEN_STYLESHEET = """
QTableWidget#MullenScoreTable {
    background-color: #182235;
    alternate-background-color: #1f2937;
    color: #e5e7eb;
    border-color: #4b5563;
    gridline-color: #374151;
}
QTableWidget#MullenScoreTable QLineEdit,
QTableWidget#MullenScoreTable QComboBox {
    background-color: #1f2937;
    color: #e5e7eb;
}
"""


def themed_stylesheet(base: str, dark_override: str, theme: str) -> str:
    return f"{base}\n{dark_override}" if theme == "Dark" else base


def application_stylesheet(theme: str) -> str:
    return themed_stylesheet(APP_STYLESHEET, DARK_APP_STYLESHEET, theme)


# MullenView: heading and subtitle overrides.
MULLEN_TITLE_STYLESHEET = "color: #111827;"
MULLEN_SUBTITLE_STYLESHEET = "color: #6b7280;"

# MullenView: scale column colors and font.
MULLEN_SCALE_BACKGROUND_COLOR = "#f8fafc"
MULLEN_SCALE_TEXT_COLOR = "#1f2937"
MULLEN_SCALE_FONT_WEIGHT = QFont.Weight.DemiBold

# MullenView: score table, headers, and input fields.
MULLEN_SCORE_TABLE_STYLESHEET = """
QTableWidget#MullenScoreTable {
    background-color: #ffffff;
    alternate-background-color: #fbfdff;
    border: 1px solid #dbe3ef;
    border-radius: 10px;
    gridline-color: #e8edf4;
    color: #1f2937;
}

QLabel#PageTitle{
    color: #111827;
}
QTableWidget#MullenScoreTable::item {
    padding: 0 14px;
}

QTableWidget#MullenScoreTable QHeaderView::section {
    background-color: #115492;
    color: #FCFCFD;
    border: 0;
    border-right: 1px solid #dbe3ef;
    border-bottom: 1px solid #cdd9e8;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 8px;
}

QTableWidget#MullenScoreTable QLineEdit {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 13px;
    padding: 7px 9px;
    margin: 9px 7px;
}

QTableWidget#MullenScoreTable QLineEdit:hover {
    border-color: #94a3b8;
}

QTableWidget#MullenScoreTable QLineEdit:focus {
    background-color: #ffffff;
    border: 2px solid #1d63ed;
    padding: 6px 8px;
}

QTableWidget#MullenScoreTable QLineEdit::placeholder {
    color: #94a3b8;
}
"""
