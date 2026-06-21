# Glassmorphic Dark Style QSS Sheet for ClipForgeAI

GLASS_STYLE = """
QMainWindow {
    background-color: #0b0b14;
    background-image: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.8, fx: 0.5, fy: 0.5, stop: 0 #18112c, stop: 1 #08070d);
}

QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* Glassmorphic Panel/Card Styling */
QFrame#glassCard {
    background-color: rgba(20, 20, 35, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

QFrame#glassSidebar {
    background-color: rgba(10, 10, 18, 0.8);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Header Text */
QLabel#headerTitle {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    background: transparent;
}

QLabel#sectionTitle {
    font-size: 18px;
    font-weight: 600;
    color: #00f0ff;
    background: transparent;
}

QLabel#bodyText {
    font-size: 13px;
    color: #94a3b8;
    background: transparent;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(0, 240, 255, 0.15);
    border: 1px solid rgba(0, 240, 255, 0.5);
}

QPushButton:pressed {
    background-color: rgba(0, 240, 255, 0.25);
}

/* Gradient Action Button */
QPushButton#primaryActionButton {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #00f0ff, stop:1 #a855f7);
    color: #0b0b14;
    border: none;
    font-weight: 700;
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 8px;
}

QPushButton#primaryActionButton:hover {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #33f3ff, stop:1 #b570fa);
}

QPushButton#primaryActionButton:pressed {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #00c6d4, stop:1 #8e3fd1);
}

/* Input Fields */
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: rgba(15, 15, 25, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 8px;
    color: #ffffff;
    selection-background-color: #a855f7;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid rgba(0, 240, 255, 0.6);
}

/* Lists and Tables */
QListWidget, QTableWidget {
    background-color: rgba(15, 15, 25, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 5px;
    gridline-color: rgba(255, 255, 255, 0.05);
}

QListWidget::item, QTableWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QListWidget::item:hover, QTableWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

QListWidget::item:selected, QTableWidget::item:selected {
    background-color: rgba(168, 85, 247, 0.3);
    border: 1px solid rgba(168, 85, 247, 0.5);
    color: #ffffff;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px 0 0px 0;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.15);
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 240, 255, 0.4);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Tab Bar Override (if standard tabs are used) */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(20, 20, 35, 0.45);
    border-radius: 16px;
}

QTabBar::tab {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: none;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #94a3b8;
    font-weight: 600;
}

QTabBar::tab:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}

QTabBar::tab:selected {
    background: rgba(20, 20, 35, 0.65);
    border-bottom: 2px solid #00f0ff;
    color: #ffffff;
}

/* Combo Box */
QComboBox {
    background-color: rgba(15, 15, 25, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 12px;
    color: #ffffff;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #0b0b14;
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: #a855f7;
    color: #ffffff;
}
"""
