# MIDI Track Generator v2

A desktop GUI application that procedurally generates genre-agnostic MIDI files using algorithmic music theory logic — not a trained AI model. Output is formatted for clean import into LMMS.

**7 tracks now available:** Bassline, Chords, Hi-Hats, Melody, Counter-Melody, Vocal Chops, and Turnaround Fills.

## 1. Dependencies

Install Python 3.11+ first, then:

```bash
pip install PyQt6 mido
```

## 2. Launch Command

Run the application from the project root directory:

```bash
py main.py
```

## 3. Features

### Generators
- **Chords** — Diatonic chord progressions with inversions, 7ths, sus chords
- **Bassline** — Rhythmic bass patterns with ghost notes, walking bass, syncopation
- **Hi-Hats** — Groove patterns with open hats, crash cymbals, 32nd-note rolls
- **Melody** — 8-bar phrase structure with motif development and rests
- **Counter-Melody** — Call-and-answer response that fills main melody gaps
- **Vocal Chops** — Monophonic lead with chromatic runs and aggressive syncopation
- **Turnaround Fills** — Chaotic chromatic fills at bar-end transitions

### GUI
- Dark mode UI with per-track enable checkboxes (all OFF by default)
- Per-track sliders: velocity range, octave shift, complexity
- Progress bar with real-time generation feedback
- Fit score display with green/yellow/red color coding
- Regenerate button for one-click re-rolls

### Fit Checker
After each generation, analyzes all 7 tracks for:
- Key/scale conformity (octave-correct)
- Harmonic clash detection
- Call-and-answer coordination
- Register separation (crowding avoidance)
- Syncopation density
- Rhythmic alignment

### LMMS Import
- Standard MIDI Type 1 files, one instrument track each
- Tempo and time signature meta events set correctly
- GM-friendly note ranges

## 4. Documentation

Read **DOCUMENTATION.md** for detailed instructions on using all features.

## 5. Output File Management

Generated MIDI files land in **OUTPUT_DEV/** in the project directory. Files are overwritten on each new generation — rename them if you want to keep a take.

## 6. License

All rights reserved. You may not sell this code without permission from the author.

---

© 2026 motdub All rights reserved.