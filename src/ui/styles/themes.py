"""
Modern UI Themes and Stylesheets for IFC Parser.
Includes Dark (default) and Light themes.
"""

DARK_THEME = """
/* Global Window & Fonts */
QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Main Cards & Containers */
QFrame#card, QWidget#card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
}

QFrame#dropZone {
    background-color: #1E293B;
    border: 2px dashed #475569;
    border-radius: 12px;
}

QFrame#dropZone:hover {
    border-color: #3B82F6;
    background-color: #1E293B;
}

/* Headers & Labels */
QLabel#headerTitle {
    font-size: 18px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel#subtitle {
    color: #94A3B8;
    font-size: 12px;
}

QLabel#kpiTitle {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#kpiValue {
    font-size: 22px;
    font-weight: bold;
    color: #F8FAFC;
}

QLabel#kpiBadgePositive {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#kpiBadgeNegative {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#kpiBadgeNeutral {
    background-color: rgba(59, 130, 246, 0.15);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton#secondaryBtn {
    background-color: #334155;
    color: #F1F5F9;
    border: 1px solid #475569;
}

QPushButton#secondaryBtn:hover {
    background-color: #475569;
    border-color: #64748B;
}

QPushButton#successBtn {
    background-color: #059669;
    color: #FFFFFF;
}

QPushButton#successBtn:hover {
    background-color: #047857;
}

QPushButton#themeToggleBtn {
    background-color: transparent;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
}

QPushButton#themeToggleBtn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
    border-color: #475569;
}

/* Inputs & Search */
QLineEdit {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 12px;
    selection-background-color: #3B82F6;
}

QLineEdit:focus {
    border-color: #3B82F6;
    outline: none;
}

/* Dropdown / ComboBox */
QComboBox {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
    min-width: 150px;
}

QComboBox:focus, QComboBox:on {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}

/* Tables */
QTableView {
    background-color: #1E293B;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #1D4ED8;
    selection-color: #FFFFFF;
    outline: none;
}

QTableView::item {
    padding: 6px 10px;
    border-bottom: 1px solid #283548;
}

QTableView::item:selected {
    background-color: #2563EB;
}

QTableView::item:hover:!selected {
    background-color: #2A384C;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px 10px;
    font-weight: 600;
    border: none;
    border-right: 1px solid #334155;
    border-bottom: 2px solid #3B82F6;
}

/* Tree / List Widget for Attributes */
QTreeWidget, QListWidget {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #F8FAFC;
    outline: none;
    padding: 4px;
}

QTreeWidget::item, QListWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #2A384C;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

/* Progress Bar */
QProgressBar {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #F8FAFC;
    font-weight: bold;
    height: 14px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #10B981);
    border-radius: 5px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #1E293B;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #60A5FA;
    border-top: 2px solid #3B82F6;
}

QTabBar::tab:hover:!selected {
    background-color: #1E293B;
    color: #F8FAFC;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #0F172A;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    min-height: 25px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0F172A;
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #334155;
    min-width: 25px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

LIGHT_THEME = """
/* Global Window & Fonts */
QWidget {
    background-color: #F8FAFC;
    color: #0F172A;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Main Cards & Containers */
QFrame#card, QWidget#card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QFrame#dropZone {
    background-color: #FFFFFF;
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
}

QFrame#dropZone:hover {
    border-color: #2563EB;
    background-color: #F1F5F9;
}

/* Headers & Labels */
QLabel#headerTitle {
    font-size: 18px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#subtitle {
    color: #64748B;
    font-size: 12px;
}

QLabel#kpiTitle {
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#kpiValue {
    font-size: 22px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#kpiBadgePositive {
    background-color: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#kpiBadgeNegative {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#kpiBadgeNeutral {
    background-color: #EFF6FF;
    color: #2563EB;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #E2E8F0;
    color: #94A3B8;
}

QPushButton#secondaryBtn {
    background-color: #F1F5F9;
    color: #1E293B;
    border: 1px solid #CBD5E1;
}

QPushButton#secondaryBtn:hover {
    background-color: #E2E8F0;
    border-color: #94A3B8;
}

QPushButton#successBtn {
    background-color: #059669;
    color: #FFFFFF;
}

QPushButton#successBtn:hover {
    background-color: #047857;
}

QPushButton#themeToggleBtn {
    background-color: transparent;
    color: #64748B;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
}

QPushButton#themeToggleBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
    border-color: #94A3B8;
}

/* Inputs & Search */
QLineEdit {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 12px;
    selection-background-color: #3B82F6;
}

QLineEdit:focus {
    border-color: #2563EB;
    outline: none;
}

/* Dropdown / ComboBox */
QComboBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
    min-width: 150px;
}

QComboBox:focus, QComboBox:on {
    border-color: #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}

/* Tables */
QTableView {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    selection-background-color: #DBEAFE;
    selection-color: #1E3A8A;
    outline: none;
}

QTableView::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}

QTableView::item:selected {
    background-color: #DBEAFE;
    color: #1E3A8A;
}

QTableView::item:hover:!selected {
    background-color: #F8FAFC;
}

QHeaderView::section {
    background-color: #F1F5F9;
    color: #475569;
    padding: 8px 10px;
    font-weight: 600;
    border: none;
    border-right: 1px solid #E2E8F0;
    border-bottom: 2px solid #2563EB;
}

/* Tree / List Widget for Attributes */
QTreeWidget, QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    color: #0F172A;
    outline: none;
    padding: 4px;
}

QTreeWidget::item, QListWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #F1F5F9;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

/* Progress Bar */
QProgressBar {
    background-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    text-align: center;
    color: #0F172A;
    font-weight: bold;
    height: 14px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #059669);
    border-radius: 5px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background-color: #FFFFFF;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #F1F5F9;
    color: #64748B;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2563EB;
    border-top: 2px solid #2563EB;
}

QTabBar::tab:hover:!selected {
    background-color: #FFFFFF;
    color: #0F172A;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #F8FAFC;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    min-height: 25px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #F8FAFC;
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    min-width: 25px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
