# Progress

## Done (all files now exist)
- main.py
- generators/common.py - shared scale/key/tempo utilities
  - GenerationConfig dataclass, get_scale_notes(), get_chord_from_scale_degree()
- generators/bassline.py - bassline generator
  - generate_bassline_progression(config, output_path), generate_bassline()
- generators/chords.py - chord progression generator
  - generate_chord_progression(config, output_path), generate_chords()
- generators/hihats.py - hi-hat rhythm generator
  - generate_hihat_pattern(config, output_path), generate_hihats()
- generators/melody.py - melody generator with chord-tone weighting
  - generate_melody_progression(config, output_path), generate_melody()
- analysis/fit_checker.py - cross-track compatibility scoring
  - check_all_tracks(), check_key_conformity(), check_harmonic_clash()
- gui/theme.py - dark theme stylesheet and palette definitions
  - DARK_THEME constant, apply_dark_theme(app)
- gui/widgets/seed_widget.py - seed control widget with Randomize button
  - SeedWidget class, get_seed(), set_seed()
- gui/main_window.py - main GUI window (just completed)
  - MainWindow class, _generate_tracks(), _open_output_folder()

## Fixes Applied (July 15)
- **generators/common.py** — Fixed `generate_midi_file()` to use correct mido API:
  - `MidiFile(type=1)` instead of `MidiFile(format=1)`
  - `MetaMessage('set_tempo', tempo=us_per_beat)` with microsecond-per-beat timing
  - Note data format changed to `List[Tuple[int, float]]` (pitch, duration_seconds)
  - Added `get_scale_notes_midi()` for pitch-based scale lookups
  - Fixed `roman_to_int` dict to include uppercase keys (I, II, III, V, VI, VII)
- **generators/chords.py** — Completely rewritten:
  - Now builds chord pitches from scale degrees with proper voicing
  - Uses `get_scale_notes_midi()` for MIDI-number-based scale notes
  - Fixed dead code after return statement
- **generators/bassline.py** — Rewritten:
  - Uses `get_scale_notes_midi()` to get MIDI pitch numbers
  - Fixed `config.scale_notes` reference that didn't exist on `GenerationConfig`
- **generators/hihats.py** — Uses correct data format `(pitch, duration)`
- **generators/melody.py** — Rewritten:
  - Moved roman numeral parsing inside function scope (was module-level `config` error)
  - Fixed `config.scale_notes` reference
  - Fixed type mismatch on `roman_to_note()` call
- **analysis/fit_checker.py** — Fixed:
  - `passed` variable scope (was unassigned on error paths)
  - Uses correct mido message attributes (`msg.note`, `msg.type`)
  - Signature matches `check_all_tracks(config, midi_files)` as called from GUI

## Verified
- All 4 generators produce valid .mid files (tested with `generate_midi_file()`)
- File sizes: chords=249B, bassline=321B, hihats=598B, melody=609B at 8 bars
- All module imports resolve without errors
