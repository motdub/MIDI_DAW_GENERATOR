"""
Main Window - PyQt6 GUI for MIDI Track Generator.
Wires together generators, fit_checker, theme, and seed_widget per AGENTS.md spec.
Dark mode mandatory implementation.
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QTextEdit, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import QSize, Qt, QUrl

# Import generators and analysis modules
from generators.common import GenerationConfig, get_scale_notes
from generators.chords import generate_chord_progression
from generators.bassline import generate_bassline_progression
from generators.hihats import generate_hihat_pattern
from generators.melody import generate_melody_progression
from analysis.fit_checker import check_all_tracks


# Color constants for UI
DARK_COLORS = {
    'background': '#1e1e1e',
    'panel_background': '#2b2b2b',
    'accent_color': '#4a9eff',
}


@dataclass
class GenerationResult:
    """Result of a generation run."""
    success: bool
    score: int
    issues: List[str]
    files_generated: Dict[str, str]  # track name -> file path


class MainWindow(QMainWindow):
    """Main window for the MIDI Track Generator application."""

    def __init__(self):
        super().__init__()

        self.config = GenerationConfig(
            root_note='C',
            scale_mode='major',
            bpm=120,
            bar_length=8
        )

        # Store generated MIDI files for later use
        self.generated_files: Dict[str, str] = {}

        # Initialize UI components
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main window UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout - horizontal (left to right)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create groups and widgets

        # Group 1: Key and Scale Selection (vertical layout)
        key_group = QGroupBox("Key & Scale")
        key_layout = QVBoxLayout(key_group)

        self.root_note_label = QLabel("Root Note:")
        self.root_note_spinbox = QSpinBox()
        self.root_note_spinbox.setRange(0, 127)
        self.root_note_spinbox.setValue(60)  # C4

        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "Major", "Natural Minor", "Dorian", "Phrygian",
            "Lydian", "Mixolydian", "Aeolian (Minor)", "Ionian"
        ])

        key_layout.addWidget(self.root_note_label)
        key_layout.addWidget(self.root_note_spinbox)
        key_layout.addWidget(self.scale_combo)

        main_layout.addWidget(key_group)

        # Group 2: Tempo and Bar Length (vertical layout)
        tempo_group = QGroupBox("Tempo & Duration")
        tempo_layout = QVBoxLayout(tempo_group)

        self.bpm_label = QLabel("BPM:")
        self.bpm_spinbox = QSpinBox()
        self.bpm_spinbox.setRange(40, 300)
        self.bpm_spinbox.setValue(self.config.bpm)

        self.bar_length_label = QLabel("Bars:")
        self.bar_length_spinbox = QSpinBox()
        self.bar_length_spinbox.setRange(1, 64)
        self.bar_length_spinbox.setValue(self.config.bar_length)

        tempo_layout.addWidget(self.bpm_label)
        tempo_layout.addWidget(self.bpm_spinbox)
        tempo_layout.addWidget(self.bar_length_label)
        tempo_layout.addWidget(self.bar_length_spinbox)

        main_layout.addWidget(tempo_group)

        # Group 3: Track Controls - Dropdown menu for Yes/No (horizontal layout)
        tracks_group = QGroupBox("Track Controls")
        tracks_layout = QHBoxLayout(tracks_group)

        self.track_controls = {}

        for track_name in ['Bassline', 'Hi-Hats', 'Chords', 'Melody']:
            # Create label and dropdown together
            name_label = QLabel(track_name + ":")
            name_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
            tracks_layout.addWidget(name_label)

            # Dropdown menu - Yes/No selection with labels
            combo = QComboBox()
            combo.addItems(["Yes", "No"])
            combo.setCurrentIndex(0)  # Default to Yes (enabled)

            # Store enabled state via user data on the combo
            combo.setCurrentIndex(0)  # 0 = Yes (enabled)

            # Make dropdown larger and more visible
            combo.setMinimumSize(150, 40)
            combo.setMaximumHeight(60)
            combo.setStyleSheet("""
                QComboBox {
                    background-color: #353535;
                    border: 2px solid #4a9eff;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QComboBox:hover {
                    background-color: #3d3d3d;
                }
            """)

            tracks_layout.addWidget(combo)

            # Store reference for later use
            self.track_controls[track_name] = {'combo': combo, 'enabled': True}

        main_layout.addWidget(tracks_group)

        # Group 4: Seed Control (vertical layout)
        seed_group = QGroupBox("Seed (Reproducibility)")
        seed_layout = QVBoxLayout(seed_group)
        seed_layout.setSpacing(12)

        self.seed_widget = None

        # Create and add the seed widget with proper sizing
        from gui.widgets.seed_widget import SeedWidget
        self.seed_widget = SeedWidget()
        self.seed_widget.setMinimumSize(350, 120)  # Minimum size for all widgets
        self.seed_widget.setMaximumSize(QSize(999999, 999999))  # Allow to grow
        seed_layout.addWidget(self.seed_widget)

        main_layout.addWidget(seed_group)

        # Set minimum size for the entire window to ensure all controls are visible
        self.setMinimumSize(1200, 700)

        # Group 5: Generate Button (vertical layout)
        generate_btn = QPushButton("Generate MIDI Tracks")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                border: 2px solid #2b5fa3;
                color: #ffffff;
                font-weight: bold;
                padding: 12px 24px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2b7fff;
            }
        """)
        generate_btn.clicked.connect(self._generate_tracks)

        main_layout.addWidget(generate_btn)

        # Group 6: Output Folder Button (vertical layout)
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        self.output_folder_btn = QPushButton("Open Output Folder")
        self.output_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b5fa3;
                border: 2px solid #1e4a9f;
                color: #ffffff;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #1e4a9f;
            }
        """)
        self.output_folder_btn.clicked.connect(self._open_output_folder)

        output_layout.addWidget(self.output_folder_btn)

        main_layout.addWidget(output_group)

        # Group 7: Log Panel (vertical layout)
        log_group = QGroupBox("Generation Log & Results")
        log_layout = QVBoxLayout(log_group)

        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 8px;
                font-family: monospace;
            }
        """)

        log_layout.addWidget(self.log_textedit)

        main_layout.addWidget(log_group)

    def _midi_to_note_name(self, midi_number: int) -> str:
        """Convert a MIDI note number (0-127) to a note name like 'C', 'C#', etc."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        idx = midi_number % 12
        return note_names[idx]

    def _get_enabled_tracks(self) -> List[str]:
        """Get list of track names that are enabled (combo set to Yes)."""
        enabled = []
        for track_name, data in self.track_controls.items():
            combo = data['combo']
            is_enabled = (combo.currentIndex() == 0)  # 0 = Yes, 1 = No
            if is_enabled:
                enabled.append(track_name)
        return enabled

    def _generate_tracks(self):
        """Generate all enabled tracks."""
        # Get configuration values
        root_note_midi = self.root_note_spinbox.value()
        root_note_name = self._midi_to_note_name(root_note_midi)

        scale_mode_map = {
            0: 'major',
            1: 'natural_minor',
            2: 'dorian',
            3: 'phrygian',
            4: 'lydian',
            5: 'mixolydian',
            6: 'aeolian',
            7: 'ionian'
        }

        scale_mode = scale_mode_map[self.scale_combo.currentIndex()]

        # Update config
        self.config.root_note = root_note_name
        self.config.scale_mode = scale_mode
        self.config.bpm = self.bpm_spinbox.value()
        self.config.bar_length = self.bar_length_spinbox.value()
        self.config.seed = self.seed_widget.get_seed() if self.seed_widget else None

        # Get enabled tracks based on Yes/No controls
        enabled_tracks = self._get_enabled_tracks()

        # Clear previous log
        self.log_textedit.clear()
        self.log_textedit.append("Starting generation...\n")
        self.log_textedit.append(f"Key: {self.config.root_note} {self.config.scale_mode}")
        self.log_textedit.append(f"BPM: {self.config.bpm}, Bars: {self.config.bar_length}\n")

        # Ensure output directory exists
        if not os.path.exists("OUTPUT_DEV"):
            os.makedirs("OUTPUT_DEV")

        # Generate each track
        generated_files = {}

        for track_name in enabled_tracks:
            try:
                file_path = f"OUTPUT_DEV/{track_name.lower().replace('-', '')}.mid"

                if track_name == 'Chords':
                    notes = generate_chord_progression(self.config, file_path)
                    self.log_textedit.append(f"[{track_name}] Generated {file_path}")
                    generated_files[track_name] = file_path

                elif track_name == 'Bassline':
                    notes = generate_bassline_progression(self.config, file_path)
                    self.log_textedit.append(f"[{track_name}] Generated {file_path}")
                    generated_files[track_name] = file_path

                elif track_name == 'Hi-Hats':
                    notes = generate_hihat_pattern(self.config, file_path)
                    self.log_textedit.append(f"[{track_name}] Generated {file_path}")
                    generated_files[track_name] = file_path

                elif track_name == 'Melody':
                    notes = generate_melody_progression(self.config, file_path)
                    self.log_textedit.append(f"[{track_name}] Generated {file_path}")
                    generated_files[track_name] = file_path

            except Exception as e:
                error_msg = f"[{track_name}] Error generating track:\n  {str(e)}\n"
                self.log_textedit.append(error_msg)
                import traceback
                self.log_textedit.append(traceback.format_exc())

        # Run fit checker on all generated files
        if len(generated_files) >= 2:
            try:
                result = check_all_tracks(self.config, generated_files)

                score_str = f"Fit Score: {result['overall_score']}/100"

                all_passed = result['passed'] and result['issues'] == ['All checks passed!']
                status_msg = 'PASS - All checks passed!' if all_passed else f'FAIL - Issues found:'

                self.log_textedit.append(f"\n{'='*50}")
                self.log_textedit.append(f"{score_str}")
                self.log_textedit.append(status_msg)

                for issue in result['issues']:
                    self.log_textedit.append(f"  - {issue}")

                self.log_textedit.append(f"\n{'='*50}\n")

            except Exception as e:
                error_msg = f"[Fit Checker] Error:\n  {str(e)}\n"
                self.log_textedit.append(error_msg)
                import traceback
                self.log_textedit.append(traceback.format_exc())

        # Update output folder button to show generated files
        self._update_output_folder_button(generated_files)

    def _update_output_folder_button(self, generated_files: Dict[str, str]):
        """Update the output folder button with generated file paths."""
        if not generated_files:
            return

        # Update button text to show files that were generated
        self.output_folder_btn.setText(f"Open Output Folder ({len(generated_files)} files)")

    def _open_output_folder(self):
        """Open the OUTPUT_DEV folder in file explorer."""
        output_dir = os.path.abspath("OUTPUT_DEV")

        # Check if directory exists, create it if not
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.log_textedit.append(f"Created {output_dir} directory\n")
            except Exception as e:
                self.log_textedit.append(f"Error creating {output_dir}: {e}\n")
                return

        # Open the folder
        try:
            url = QUrl.fromLocalFile(output_dir)
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)
        except Exception as e:
            self.log_textedit.append(f"Error opening folder: {e}\n")


def main():
    """Launch the GUI application."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Apply dark theme to ensure consistent dark mode regardless of OS settings
    from gui.theme import DARK_THEME, apply_dark_theme
    apply_dark_theme(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()