"""
Dark Theme - Provides stylesheet and palette definitions for consistent dark UI.
Mandatory dark mode implementation per AGENTS.md spec.
"""

from PyQt6.QtWidgets import QApplication


# Dark color palette values (hex)
DARK_COLORS = {
    'background': '#1e1e1e',      # Main background
    'panel_background': '#2b2b2b',  # Panel backgrounds
    'widget_background': '#353535',  # Widget backgrounds
    'text_primary': '#ffffff',       # Primary text (white)
    'text_secondary': '#aaaaaa',     # Secondary text (gray)
    'accent_color': '#4a9eff',       # Blue accent color
    'button_background': '#2b2b2b',  # Button background
    'button_hover': '#3d3d3d',       # Button hover
    'border_color': '#444444',       # Border color
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

QCheckBox {
    color: #ffffff;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #353535;
    border: 1px solid #444444;
}

QCheckBox::indicator:checked {
    background-color: #353535;
    border: 1px solid #444444;
}

QGroupBox {
    font-weight: bold; color: #ffffff
    color: #ffffff;
    border: 2px solid #4a9eff;
    border-radius: 6px; color: #ffffff;
    margin-top: 12px; padding-left: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 0px;
    padding: 4px 8px;
}

QScrollArea {
    background-color: #353535;
    border: 1px solid #444444;
}

QScrollBar:vertical {
    width: 16px;
    background-color: #353535;
    border: 1px solid #444444;
}

QScrollBar::handle:vertical {
    background-color: #353535;
    border-radius: 8px;
    margin: 0px 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSplitter::handle {
    background-color: #353535;
}

QTextEdit, QPlainTextEdit {
    background-color: #353535;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 8px;
}

QTabWidget::pane {
    border: 1px solid #444444;
    border-radius: 6px; color: #ffffff;
}

QTabBar::tab {
    background-color: #353535;
    color: #ffffff;
    border-right: 1px solid #4a9eff;
    padding: 8px 12px;
    margin-top: 4px;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #353535;
}

QProgressBar {
    border: 1px solid #444444;
    border-radius: 4px;
    text-align: center;
    font-weight: bold; color: #ffffff
    color: #ffffff;
    background-color: #353535;
}

QProgressBar::chunk {
    background-color: #353535;
}

QFrame {
    background-color: #353535;
}

QLabel {
    color: #ffffff;
}

QFrame#log_panel {
    background-color: #353535;
    border: 1px solid #444444;
    padding: 8px;
}

QFrame#output_folder_button {
    background-color: #353535;
    border: 2px solid #4a9eff;
    color: #ffffff;
    font-weight: bold; color: #ffffff
    padding: 10px 20px;
    min-width: 150px;
}

QFrame#output_folder_button:hover {
    background-color: #353535;
}

"""


def apply_dark_theme(app: QApplication) -> None:
    """Apply the dark theme to a PyQt6 application."""
    app.setStyleSheet(DARK_THEME.format(**DARK_COLORS))


if __name__ == "__main__":
    # Test the theme
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    
    print("Dark theme applied successfully!")
    print(f"Colors: {DARK_COLORS}")
