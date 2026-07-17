# MIDI DAW GENERATOR

A desktop GUI application that procedurally generates genre-agnostic MIDI files (bassline, hi-hats, chords, melody) using algorithmic music theory logic. Built with Python, PyQt6, and mido/pretty_midi. Output is formatted for clean import into LMMS.

## 1. Dependencies

Install the following Python packages for this program to work:

```bash
pip install PyQt6 mido pretty_midi
```

Requires Python 3.11+.

## 2. Launch Command

Run the application from the project root directory:

```bash
python main.py
```

## 3. Documentation

Read the **DOCUMENTATION.md** file in this GitHub repository for detailed instructions on how to use this program, including:

- Selecting key, tempo, and bar length
- Per-track enable/disable
- Generation and fit checking
- Understanding the output files

## 4. Output File Management

After generation completes inside the project directory, open the **OUTPUT_DEV/** folder and rename the `.mid` files if you want to keep them — they will be overwritten the next time you generate notes with a different generation seed.

## 5. License

All rights reserved. You may not sell this code without permission from the author.

---

© 2026 Matt Dubois. All rights reserved.