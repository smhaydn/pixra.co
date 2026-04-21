"""
Ticimax AI Manager — Tema/Stil Tanimlari
Tum PyQt6 QSS (Qt Style Sheet) tanimlari bu dosyada merkezlestirilmistir.
"""

DARK_THEME_QSS = """
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1a1a2e;
}
QGroupBox {
    border: 1px solid #3a3a5c;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    color: #00BFA6;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
}
QLineEdit {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #00BFA6;
}
QLineEdit:focus {
    border: 1px solid #00BFA6;
}
QPushButton {
    background-color: #00BFA6;
    color: #1a1a2e;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #00D4B8;
}
QPushButton:pressed {
    background-color: #009688;
}
QPushButton:disabled {
    background-color: #3a3a5c;
    color: #6e6e8a;
}
QPushButton#dangerBtn {
    background-color: #e74c3c;
    color: #ffffff;
}
QPushButton#dangerBtn:hover {
    background-color: #ff6b6b;
}
QTabWidget::pane {
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    background-color: #16213e;
}
QTabBar::tab {
    background-color: #1a1a2e;
    color: #8e8ea0;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #16213e;
    color: #00BFA6;
    border-bottom: 2px solid #00BFA6;
}
QTableWidget {
    background-color: #16213e;
    gridline-color: #3a3a5c;
    border-radius: 6px;
    border: 1px solid #3a3a5c;
    selection-background-color: #0a3d5c;
}
QHeaderView::section {
    background-color: #1a1a2e;
    color: #00BFA6;
    padding: 8px;
    border: 1px solid #3a3a5c;
    font-weight: bold;
}
QTextEdit {
    background-color: #0f0f23;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    color: #a0ffa0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
}
QProgressBar {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    height: 22px;
}
QProgressBar::chunk {
    background-color: #00BFA6;
    border-radius: 5px;
}
QSplitter::handle {
    background-color: #3a3a5c;
    height: 2px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a3a5c;
    background-color: #16213e;
}
QCheckBox::indicator:checked {
    background-color: #00BFA6;
    border-color: #00BFA6;
}
QComboBox {
    background-color: #16213e;
    border: 1px solid #3a3a5c;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    min-height: 20px;
}
QComboBox:hover {
    border: 1px solid #00BFA6;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #3a3a5c;
    selection-background-color: #00BFA6;
    selection-color: #1a1a2e;
}
"""
