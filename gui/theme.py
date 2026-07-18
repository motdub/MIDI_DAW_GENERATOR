"""
Dark Theme - Provides stylesheet and palette definitions for consistent dark UI.
Mandatory dark mode implementation per AGENTS.md spec.
"""

from PyQt6.QtWidgets import QApplication


# Dark color palette values (hex)
DARK_COLORS = {
    'background': '#1e1e1e',          # Main background
    'panel_background': '#2b2b2b',    # Panel backgrounds
    'widget_background': '#353535',   # Widget backgrounds
    'text_primary': '#ffffff',        # Primary text (white)
    'text_secondary': '#aaaaaa',      # Secondary text (gray)
    'accent_color': '#4a9eff',        # Blue accent color
    'button_background': '#2b2b2b',   # Button background
    'button_hover': '#3d3d3d',        # Button hover
    'border_color': '#444444',         # Border color
}

# Dark theme stylesheet (hardcoded colors for reliability)
DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: Arial, sans-serif;
    font-size: 12px;
}

QPushButton {
    background-color: #2b2b2b;
    border: 1px solid #444444;
    color: #ffffff;
    padding: 8px 16px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #3d3d3d;
}

QPushButton:pressed {
    background-color: #2b5fa3;
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #353535;
    border: 1px solid #444444;
    color: #ffffff;
    padding: 6px;
    selection-background-color: #353535;
}

QComboBox {
    background-color: #353535;
    border: 1px solid #444444;
    color: #ffffff;
    padding: 6px;
}

QComboBox::drop-down {
    border: none;
    background: #353535;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #aaaaaa;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #353535;
    border: 1px solid #444444;
    color: #ffffff;
    selection-background-color: #4a9eff;
}

QCheckBox {
    color: #ffffff;
    spacing: 8px;
    padding: 4px 0px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #353535;
    border: 1px solid #444444;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border: 1px solid #2b7fff;
}

QCheckBox::indicator:hover {
    background-color: #3d3d3d;
    border: 1px solid #4a9eff;
}

QGroupBox {
    font-weight: bold;
    color: #ffffff;
    border: 2px solid #4a9eff;
    border-radius: 6px;
    margin-top: 12px;
    padding-left: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 0px;
    padding: 4px 8px;
    color: #ffffff;
    font-weight: bold;
}

QScrollArea {
    background-color: #353535;
    border: 1px solid #444444;
}

QScrollBar:vertical {
    width: 16px;
    background-color: #2b2b2b;
    border: 1px solid #444444;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 8px;
    margin: 2px 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 16px;
    background-color: #2b2b2b;
    border: 1px solid #444444;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 8px;
    margin: 4px 2px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QSplitter::handle {
    background-color: #444444;
    width: 4px;
    height: 4px;
}

QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 8px;
    font-family: monospace;
}

QTabWidget::pane {
    border: 1px solid #444444;
    border-radius: 4px;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #353535;
    color: #aaaaaa;
    padding: 8px 16px;
    margin-top: 4px;
    min-width: 80px;
    border: 1px solid #444444;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    color: #ffffff;
    border-bottom: 2px solid #4a9eff;
}

QTabBar::tab:hover {
    background-color: #3d3d3d;
    color: #ffffff;
}

QProgressBar {
    border: 1px solid #444444;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    background-color: #353535;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 3px;
}

QSlider::groove:horizontal {
    border: 1px solid #444444;
    height: 6px;
    background-color: #353535;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #4a9eff;
    border: 1px solid #2b7fff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background-color: #2b7fff;
}

QSlider::sub-page:horizontal {
    background-color: #4a9eff;
    border-radius: 3px;
}

QSlider::groove:vertical {
    border: 1px solid #444444;
    width: 6px;
    background-color: #353535;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background-color: #4a9eff;
    border: 1px solid #2b7fff;
    width: 14px;
    height: 14px;
    margin: 0 -5px;
    border-radius: 7px;
}

QSlider::handle:vertical:hover {
    background-color: #2b7fff;
}

QSlider::sub-page:vertical {
    background-color: #4a9eff;
    border-radius: 3px;
}

QLabel {
    color: #ffffff;
}

QFrame#log_panel {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    padding: 8px;
}

QFrame#output_folder_button {
    background-color: #353535;
    border: 2px solid #4a9eff;
    color: #ffffff;
    font-weight: bold;
    padding: 10px 20px;
    min-width: 150px;
}

QFrame#output_folder_button:hover {
    background-color: #3d3d3d;
}

QListWidget {
    background-color: #353535;
    border: 1px solid #444444;
    color: #ffffff;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}

QMenuBar {
    background-color: #2b2b2b;
    color: #ffffff;
    border-bottom: 1px solid #444444;
}

QMenuBar::item:selected {
    background-color: #353535;
}

QMenu {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #444444;
}

QMenu::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}
"""


def apply_dark_theme(app: QApplication) -> None:
    """Apply the dark theme to a PyQt6 application."""
    app.setStyleSheet(DARK_THEME.format(**DARK_COLORS))