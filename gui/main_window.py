"""
Main Window - PyQt6 GUI for MIDI Track Generator (v2).
Enhanced with new tracks, checkboxes, per-track controls, and fit score display.

Wires together all generators, fit_checker, theme, and seed_widget.
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QSlider, QTextEdit, QFileDialog, QMessageBox,
    QScrollArea, QGridLayout, QProgressBar, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QUrl, QTimer

# Import generators and analysis modules
from generators.common import (
    GenerationConfig, TrackConfig, build_chord_progression,
    get_scale_notes_midi
)
from generators.chords import generate_chord_progression
from generators.bassline import generate_bassline_progression
from generators.hihats import generate_hihat_pattern
from generators.melody import generate_melody_progression
from generators.counter_melody import generate_counter_melody_progression
from generators.vocal_chops import generate_vocal_chops_progression
from generators.turnaround_fills import generate_turnaround_fills_progression, get_melody_blank_positions
from analysis.fit_checker import check_all_tracks


# Color constants for UI
DARK_COLORS = {
    'background': '#1e1e1e',
    'panel_background': '#2b2b2b',
    'accent_color': '#4a9eff',
    'green': '#4caf50',
    'yellow': '#ff9800',
    'red': '#f44336',
}

# Track definitions: name -> (color, default_velocity_min, default_velocity_max, default_complexity)
TRACK_DEFS = {
    'Bassline': ('#ff9800', 60, 95, 0.5),
    'Chords': ('#4a9eff', 40, 85, 0.5),
    'Hi-Hats': ('#9c27b0', 20, 127, 0.6),
    'Melody': ('#4caf50', 50, 100, 0.7),
    'Counter-Melody': ('#e91e63', 60, 100, 0.6),
    'Vocal Chops': ('#ff5722', 70, 110, 0.8),
    'Turnaround Fills': ('#00bcd4', 80, 120, 0.9),
}


@dataclass
class GenerationResult:
    """Result of a generation run."""
    success: bool
    score: int
    issues: List[str]
    files_generated: Dict[str, str]


class MainWindow(QMainWindow):
    """Main window for the MIDI Track Generator application (v2)."""

    def __init__(self):
        super().__init__()

        self.config = GenerationConfig(
            root_note='C',
            scale_mode='major',
            bpm=128,
            bar_length=16
        )

        # Store generated MIDI files for later use
        self.generated_files: Dict[str, str] = {}
        self.generated_notes: Dict[str, List[Tuple[int, float, int]]] = {}

        # Per-track widget references
        self.track_checkboxes: Dict[str, QCheckBox] = {}
        self.track_velocity_min: Dict[str, QSlider] = {}
        self.track_velocity_max: Dict[str, QSlider] = {}
        self.track_octave_shift: Dict[str, QSlider] = {}
        self.track_complexity: Dict[str, QSlider] = {}
        self.track_control_widgets: Dict[str, QWidget] = {}

        # Initialize UI components
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main window UI with organized sections."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout - vertical with scroll area
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title_label = QLabel("🎹 MIDI Track Generator v2")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; padding: 8px;")
        main_layout.addWidget(title_label)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # === Section 1: Song Settings ===
        settings_group = QGroupBox("Song Settings")
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setSpacing(20)

        # Root Note combo
        root_layout = QVBoxLayout()
        root_layout.addWidget(QLabel("Root Note:"))
        self.root_note_combo = QComboBox()
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.root_note_combo.addItems(note_names)
        self.root_note_combo.setCurrentText('C')
        self.root_note_combo.setMinimumWidth(80)
        root_layout.addWidget(self.root_note_combo)
        settings_layout.addLayout(root_layout)

        # Scale combo
        scale_layout = QVBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "Major", "Natural Minor", "Dorian", "Phrygian",
            "Lydian", "Mixolydian", "Aeolian", "Ionian"
        ])
        self.scale_combo.setMinimumWidth(120)
        scale_layout.addWidget(self.scale_combo)
        settings_layout.addLayout(scale_layout)

        # BPM spin
        bpm_layout = QVBoxLayout()
        bpm_layout.addWidget(QLabel("BPM:"))
        self.bpm_spinbox = QSpinBox()
        self.bpm_spinbox.setRange(40, 300)
        self.bpm_spinbox.setValue(128)
        self.bpm_spinbox.setMinimumWidth(80)
        bpm_layout.addWidget(self.bpm_spinbox)
        settings_layout.addLayout(bpm_layout)

        # Bars spin
        bars_layout = QVBoxLayout()
        bars_layout.addWidget(QLabel("Bars:"))
        self.bar_length_spinbox = QSpinBox()
        self.bar_length_spinbox.setRange(1, 64)
        self.bar_length_spinbox.setValue(16)
        self.bar_length_spinbox.setMinimumWidth(80)
        bars_layout.addWidget(self.bar_length_spinbox)
        settings_layout.addLayout(bars_layout)

        # Seed widget
        from gui.widgets.seed_widget import SeedWidget
        self.seed_widget = SeedWidget()
        settings_layout.addWidget(self.seed_widget)

        settings_layout.addStretch()
        scroll_layout.addWidget(settings_group)

        # === Section 2: Track Enables ===
        tracks_group = QGroupBox("Track Enables")
        tracks_layout = QVBoxLayout(tracks_group)

        # Grid of checkboxes with colored indicators
        track_grid = QGridLayout()
        track_grid.setSpacing(8)

        for i, (track_name, (color, vel_min, vel_max, complexity)) in enumerate(TRACK_DEFS.items()):
            row = i // 4
            col = i % 4

            track_widget = QWidget()
            track_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: #2b2b2b;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)
            track_inner = QHBoxLayout(track_widget)
            track_inner.setContentsMargins(8, 4, 8, 4)

            # Color indicator dot
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"""
                background-color: {color};
                border-radius: 6px;
                min-width: 12px;
                min-height: 12px;
            """)
            track_inner.addWidget(dot)

            # Checkbox
            cb = QCheckBox(track_name)
            cb.setChecked(False)  # All OFF by default
            self.track_checkboxes[track_name] = cb
            track_inner.addWidget(cb)
            track_inner.addStretch()

            track_grid.addWidget(track_widget, row, col)

        tracks_layout.addLayout(track_grid)
        scroll_layout.addWidget(tracks_group)

        # === Section 3: Per-Track Controls (expandable) ===
        controls_group = QGroupBox("Per-Track Controls")
        controls_layout = QVBoxLayout(controls_group)

        for track_name, (color, vel_min, vel_max, complexity) in TRACK_DEFS.items():
            track_control = self._create_track_control(track_name, color, vel_min, vel_max, complexity)
            self.track_control_widgets[track_name] = track_control
            controls_layout.addWidget(track_control)

        scroll_layout.addWidget(controls_group)

        # === Section 4: Generate & Output ===
        action_group = QGroupBox("Generate & Output")
        action_layout = QVBoxLayout(action_group)

        # Top row: buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        self.generate_btn = QPushButton("🎵 Generate All Enabled")
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #4a9eff;
                border: 2px solid #2b7fff;
                color: #ffffff;
                font-weight: bold;
                padding: 14px 28px;
                min-width: 220px;
                font-size: 16px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #2b7fff;
            }}
            QPushButton:pressed {{
                background-color: #1a6fff;
            }}
        """)
        self.generate_btn.clicked.connect(self._generate_tracks)
        button_row.addWidget(self.generate_btn)

        self.regenerate_btn = QPushButton("🔄 Regenerate All")
        self.regenerate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff9800;
                border: 2px solid #e68900;
                color: #ffffff;
                font-weight: bold;
                padding: 14px 28px;
                min-width: 180px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #e68900;
            }}
        """)
        self.regenerate_btn.clicked.connect(self._generate_tracks)
        self.regenerate_btn.setVisible(False)
        button_row.addWidget(self.regenerate_btn)

        self.output_btn = QPushButton("📁 Open Output Folder")
        self.output_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2b5fa3;
                border: 2px solid #1e4a9f;
                color: #ffffff;
                font-weight: bold;
                padding: 14px 28px;
                min-width: 180px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #1e4a9f;
            }}
        """)
        self.output_btn.clicked.connect(self._open_output_folder)
        button_row.addWidget(self.output_btn)

        button_row.addStretch()
        action_layout.addLayout(button_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(24)
        action_layout.addWidget(self.progress_bar)

        # Fit score display
        self.score_frame = QFrame()
        self.score_frame.setFixedHeight(60)
        self.score_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #2b2b2b;
                border: 2px solid #444444;
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        score_layout = QHBoxLayout(self.score_frame)

        self.score_label = QLabel("Fit Score: --")
        self.score_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #aaaaaa;")
        score_layout.addWidget(self.score_label)

        self.score_status = QLabel("No generation yet")
        self.score_status.setStyleSheet("font-size: 14px; color: #888888;")
        score_layout.addWidget(self.score_status)

        score_layout.addStretch()
        self.score_frame.setVisible(False)
        action_layout.addWidget(self.score_frame)

        scroll_layout.addWidget(action_group)

        # === Section 5: Log Panel ===
        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout(log_group)

        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setMinimumHeight(150)
        self.log_textedit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 8px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        log_layout.addWidget(self.log_textedit)

        scroll_layout.addWidget(log_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Window properties
        self.setWindowTitle("MIDI Track Generator v2")
        self.setMinimumSize(1000, 800)
        self.resize(1200, 900)

    def _create_track_control(self, track_name: str, color: str,
                              vel_min: int, vel_max: int,
                              complexity: float) -> QWidget:
        """Create expandable per-track control panel."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        layout = QGridLayout(widget)
        layout.setSpacing(8)

        # Color dot + name
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px; min-width: 10px; min-height: 10px;")
        layout.addWidget(dot, 0, 0)

        name_label = QLabel(track_name)
        name_label.setStyleSheet("font-weight: bold; color: #ffffff; background: transparent;")
        layout.addWidget(name_label, 0, 1)

        # Velocity Min
        layout.addWidget(QLabel("Vel Min:"), 0, 2)
        vel_min_slider = QSlider(Qt.Orientation.Horizontal)
        vel_min_slider.setRange(0, 127)
        vel_min_slider.setValue(vel_min)
        vel_min_slider.setFixedWidth(100)
        self.track_velocity_min[track_name] = vel_min_slider
        layout.addWidget(vel_min_slider, 0, 3)

        # Velocity Max
        layout.addWidget(QLabel("Vel Max:"), 0, 4)
        vel_max_slider = QSlider(Qt.Orientation.Horizontal)
        vel_max_slider.setRange(0, 127)
        vel_max_slider.setValue(vel_max)
        vel_max_slider.setFixedWidth(100)
        self.track_velocity_max[track_name] = vel_max_slider
        layout.addWidget(vel_max_slider, 0, 5)

        # Octave Shift
        layout.addWidget(QLabel("Octave:"), 0, 6)
        octave_slider = QSlider(Qt.Orientation.Horizontal)
        octave_slider.setRange(-2, 2)
        octave_slider.setValue(0)
        octave_slider.setFixedWidth(80)
        octave_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        octave_slider.setTickInterval(1)
        self.track_octave_shift[track_name] = octave_slider
        layout.addWidget(octave_slider, 0, 7)

        # Complexity
        layout.addWidget(QLabel("Complexity:"), 0, 8)
        complexity_slider = QSlider(Qt.Orientation.Horizontal)
        complexity_slider.setRange(0, 100)
        complexity_slider.setValue(int(complexity * 100))
        complexity_slider.setFixedWidth(100)
        self.track_complexity[track_name] = complexity_slider
        layout.addWidget(complexity_slider, 0, 9)

        layout.setColumnStretch(10, 1)
        widget.setVisible(True)
        return widget

    def _get_enabled_tracks(self) -> List[str]:
        """Get list of track names that are enabled (checkbox checked)."""
        return [name for name, cb in self.track_checkboxes.items() if cb.isChecked()]

    def _get_config_from_ui(self) -> GenerationConfig:
        """Build a GenerationConfig from current UI values."""
        root_note = self.root_note_combo.currentText()

        scale_mode_map = {
            0: 'major', 1: 'natural_minor', 2: 'dorian', 3: 'phrygian',
            4: 'lydian', 5: 'mixolydian', 6: 'aeolian', 7: 'ionian'
        }
        scale_mode = scale_mode_map[self.scale_combo.currentIndex()]

        config = GenerationConfig(
            root_note=root_note,
            scale_mode=scale_mode,
            bpm=self.bpm_spinbox.value(),
            bar_length=self.bar_length_spinbox.value(),
            seed=self.seed_widget.get_seed() if self.seed_widget else None
        )

        # Add per-track configs
        for track_name in TRACK_DEFS.keys():
            config.track_configs[track_name] = TrackConfig(
                enabled=track_name in self._get_enabled_tracks(),
                velocity_min=self.track_velocity_min[track_name].value(),
                velocity_max=self.track_velocity_max[track_name].value(),
                octave_shift=self.track_octave_shift[track_name].value(),
                complexity=self.track_complexity[track_name].value() / 100.0
            )

        return config

    def _generate_tracks(self):
        """Generate all enabled tracks."""
        config = self._get_config_from_ui()
        enabled_tracks = self._get_enabled_tracks()

        if not enabled_tracks:
            self._log("⚠️ No tracks enabled! Check at least one track.")
            return

        # Clear previous
        self.log_textedit.clear()
        self.generated_files = {}
        self.generated_notes = {}

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.score_frame.setVisible(False)
        self.regenerate_btn.setVisible(False)

        self._log(f"🎵 Starting generation with {len(enabled_tracks)} tracks...")
        self._log(f"  Key: {config.root_note} {config.scale_mode}")
        self._log(f"  BPM: {config.bpm}, Bars: {config.bar_length}")
        if config.seed:
            self._log(f"  Seed: {config.seed}")
        self._log("")

        # Ensure output directory exists
        if not os.path.exists("OUTPUT_DEV"):
            os.makedirs("OUTPUT_DEV")

        # Build chord progression once for cross-track coordination
        chord_progression = build_chord_progression(config)

        track_order = [
            ('Chords', generate_chord_progression),
            ('Bassline', generate_bassline_progression),
            ('Hi-Hats', generate_hihat_pattern),
            ('Melody', generate_melody_progression),
            ('Counter-Melody', generate_counter_melody_progression),
            ('Vocal Chops', generate_vocal_chops_progression),
            ('Turnaround Fills', generate_turnaround_fills_progression),
        ]

        # Generate each track
        total_steps = len([t for t in track_order if t[0] in enabled_tracks])
        current_step = 0

        for track_name, gen_func in track_order:
            if track_name not in enabled_tracks:
                continue

            try:
                file_path = f"OUTPUT_DEV/{track_name.lower().replace(' ', '_').replace('-', '')}.mid"

                self._log(f"[{track_name}] Generating...")

                # Handle special cases
                if track_name == 'Counter-Melody':
                    main_melody = self.generated_notes.get('Melody', None)
                    notes = gen_func(config, file_path, main_melody)
                elif track_name == 'Turnaround Fills':
                    notes = gen_func(config, file_path)
                else:
                    notes = gen_func(config, file_path)

                self.generated_notes[track_name] = notes
                self.generated_files[track_name] = file_path
                self._log(f"  ✅ Saved: {file_path}")

            except Exception as e:
                error_msg = f"[{track_name}] Error:\n  {str(e)}\n"
                self._log(error_msg)
                import traceback
                self._log(traceback.format_exc())

            current_step += 1
            self.progress_bar.setValue(int((current_step / total_steps) * 80))

        # Run fit checker
        if len(self.generated_files) >= 2:
            self._log(f"\n{'='*50}")
            self._log("🔍 Running fit check...")
            self.progress_bar.setValue(85)

            try:
                result = check_all_tracks(config, self.generated_files)
                self._display_fit_score(result)
            except Exception as e:
                self._log(f"[Fit Checker] Error: {e}")

        self.progress_bar.setValue(100)
        self._log(f"\n{'='*50}")
        self._log(f"✅ Generation complete! {len(self.generated_files)} files created.")

        # Show regenerate button
        self.regenerate_btn.setVisible(True)
        self.output_btn.setText(f"📁 Open Output Folder ({len(self.generated_files)} files)")

        # Auto-hide progress after 3 seconds
        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))

    def _display_fit_score(self, result: dict):
        """Display fit score with color coding."""
        score = result['overall_score']
        issues = result['issues']

        self.score_frame.setVisible(True)

        # Color coding
        if score >= 80:
            color = '#4caf50'  # green
            status = "Excellent!"
        elif score >= 60:
            color = '#ff9800'  # yellow
            status = "Good — could improve"
        else:
            color = '#f44336'  # red
            status = "Needs improvement — consider regenerating"

        self.score_label.setText(f"Fit Score: {score}/100")
        self.score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        self.score_status.setText(status)
        self.score_status.setStyleSheet(f"font-size: 14px; color: {color};")

        self._log(f"\n📊 Fit Score: {score}/100 — {status}")
        for issue in issues:
            self._log(f"  • {issue}")

        # If score < 50, suggest regeneration
        if score < 50:
            self._log("\n⚠️ Score is low — try clicking 'Regenerate All' for different results.")

    def _log(self, message: str):
        """Append a message to the log panel."""
        self.log_textedit.append(message)
        # Auto-scroll to bottom
        cursor = self.log_textedit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_textedit.setTextCursor(cursor)

    def _open_output_folder(self):
        """Open the OUTPUT_DEV folder in file explorer."""
        output_dir = os.path.abspath("OUTPUT_DEV")

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self._log(f"Error creating {output_dir}: {e}")
                return

        try:
            url = QUrl.fromLocalFile(output_dir)
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)
        except Exception as e:
            self._log(f"Error opening folder: {e}")


def main():
    """Launch the GUI application."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Apply dark theme
    from gui.theme import apply_dark_theme
    apply_dark_theme(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()