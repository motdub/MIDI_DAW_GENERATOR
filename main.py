"""
MIDI Track Generator - Main Entry Point
Generates procedural MIDI files (bassline, hi-hats, chords, melody) for LMMS import.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    """Launch the GUI application."""
    app = QApplication(sys.argv)
    
    # Apply dark theme to ensure consistent dark mode regardless of OS settings
    from gui.theme import DARK_THEME
    app.setStyleSheet(DARK_THEME)
    
    # Create and show main window
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
