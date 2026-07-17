# MIDI Track Generator - User Guide

## Quick Start
1. Run `py main.py` to launch the application
2. Configure your settings (see below)
3. Click **"Generate MIDI Tracks"**
4. Files will be saved in the **OUTPUT_DEV/** folder
5. Click **"Open Output Folder"** to view your generated MIDI files

---

## Understanding Music Terms

### Root Note
- The **root note** is the tonal center or "home" of your music
- In this tool, it's selected as a MIDI note number (0-127)
- **MIDI 60 = C4** (middle C on most keyboards)
- Other common roots:
  - MIDI 67 = G4 (G is the root key for many pianos)
  - MIDI 69 = A4 (A is standard tuning pitch)
  - MIDI 71 = B4

### Scale Modes
The scale determines which notes are "in tune" for your music:

| Mode | Description | Example Notes (C major) | Use Case |
|------|-------------|-------------------------|----------|
| **Major** | Bright, happy, uplifting | C D E F G A B | Pop, rock, classical |
| **Natural Minor** | Sad, serious, emotional | C D E♭ F G A♭ B♭ | Ballads, melancholy |
| **Dorian** | Jazz-like, minor but bright | C D E♭ F G A♮ B♭ | Funk, jazz, hip-hop |
| **Phrygian** | Spanish, exotic, tense | C D♭ E♭ F G A♭ B♭ | Flamenco, rock |
| **Lydian** | Dreamy, floating, major-ish | C D E F♯ G A B | Jazz, fantasy music |
| **Mixolydian** | Bluesy, dominant 7th feel | C D E F G A♭ B♮ | Rock, blues, jazz |
| **Aeolian (Minor)** | Same as natural minor | C D E♭ F G A♭ B♭ | Standard minor key |
| **Ionian** | Same as major | C D E F G A B | Major key alternative |

### BPM (Beats Per Minute)
- Controls the **tempo** or speed of your music
- **120 BPM** = moderate tempo, common for pop/rock
- **60-80 BPM** = slow ballads
- **140+ BPM** = fast electronic/trance

### Bars (Measures)
- A "bar" is a measure in music notation
- **8 bars** = 2 full musical phrases, typical for short demos
- **16 bars** = standard song length section
- More bars = longer generated track

---

## Track Types Explained

Each generator creates a separate MIDI file with its own instrument.

### Chords (chords.mid)
- Creates **harmonic backing** - the chord progression that supports your melody
- Each bar gets one chord (e.g., C major, G7, Am, F)
- Voice: Piano-like chords in octaves 3-4
- Think of this as the "background harmony"

### Bassline (bassline.mid)
- Creates a **rhythmic bass pattern** that locks with the chord changes
- Plays root notes on strong beats, sometimes fifths for variation
- Voice: Low register (octaves 2-3), single note per beat
- Think of this as the "walking bass" line

### Hi-Hats (hihats.mid)
- Creates a **rhythmic percussion pattern**
- Steady 8th/16th notes with occasional syncopation
- Voice: Single pitch (GM closed hi-hat), focuses on rhythm and velocity
- Think of this as the "drum machine" beat

### Melody (melody.mid)
- Creates a **lead melody line** over the chord progression
- Uses chord tones on strong beats, passing notes on weak beats
- Voice: Mid register (octaves 3-4), melodic contour rules applied
- Think of this as your "singing voice" or lead instrument

---

## Seed Control

### What is a seed?
A **seed** is a number that controls randomness in the generation process.

### Why use it?
- **Seed = 0 (default)**: Generates different results each time
- **Set specific seed**: Get identical results every time you generate
- Useful for: Trying multiple variations, saving your favorite version

### How to use:
1. Click **"Randomize Seed"** button to get a new random number
2. Or manually enter any number (0 to 2,147,483,647)
3. The seed affects note selection, rhythm variation, and chord choices

---

## Track Enable/Disable Checkboxes

Each track has an enable checkbox:

| Checkbox | What it does | When you'd disable it |
|----------|--------------|----------------------|
| **Bassline** | Generates bass.mid file | If you want only chords + melody, or if your DAW already has a bass track |
| **Hi-Hats** | Generates hihats.mid file | If you don't need percussion, or have your own drums |
| **Chords** | Generates chords.mid file | Rarely - this provides harmonic foundation |
| **Melody** | Generates melody.mid file | Only if you want to focus on harmony only |

---

## Output Files

### How many files are created?
- **4 files total**: `bassline.mid`, `chihats.mid`, `chords.mid`, `melody.mid`
- Each file is a separate MIDI track (one instrument per file)
- All files share the same tempo and time signature for LMMS sync

### File format
- **MIDI Type 1** - Single-track format, easy to import into DAWs
- Compatible with: LMMS, Ableton Live, FL Studio, Reaper, etc.
- Each file can be imported as a separate instrument track

---

## How Results Differ

### Every generation is different (unless you set the same seed)
The generators use algorithmic randomness for:
1. **Chord progression variation** - Different common progressions each time
2. **Note selection** - Slight variations in which scale notes are chosen
3. **Rhythm syncopation** - Hi-hats may have different accent patterns
4. **Melody contour** - Different melodic shapes and phrasing

### To get the same results:
1. Set a specific seed value (e.g., 12345)
2. Keep all other settings identical
3. Generate again → You'll get the exact same MIDI files

---

## Example Workflow

### Demo 1: Quick Pop Track
- Root Note: **C** (MIDI 60)
- Scale: **Major**
- BPM: **120**
- Bars: **8**
- Seed: Leave at **0** (random each time)
- All tracks enabled

### Demo 2: Sad Ballad
- Root Note: **A** (MIDI 69)
- Scale: **Natural Minor**
- BPM: **75**
- Bars: **16**
- Seed: Set to **42** for reproducibility
- Enable all tracks

### Demo 3: Minimal Jazz
- Root Note: **D** (MIDI 62)
- Scale: **Dorian**
- BPM: **90**
- Bars: **8**
- Seed: Randomize once, then keep fixed
- Disable Hi-Hats (you have your own drums)

---

## Troubleshooting

### "Fit Score" is low (< 70/100)
The fit checker analyzes your generation for issues like:
- Notes outside the selected scale
- Dissonant intervals between melody and chords
- Bassline not aligning with chord changes
- Register crowding (too many notes in same octave range)

**Solution**: Try a different seed or regenerate to get better results.

### Files won't import into my DAW
Ensure:
1. All files are in OUTPUT_DEV/ folder
2. Each file has proper tempo meta events (set automatically)
3. Notes are within standard GM ranges (avoid extreme octaves)

---

## Technical Details (Optional)

### MIDI Note Numbers
- Range: 0 (C0, lowest C) to 127 (E8, highest E)
- Each semitone = 1 note number
- Octave 4 is middle range (C4-D4-E4-F4...)

### Register Ranges
| Track | MIDI Note Range | Description |
|-------|-----------------|-------------|
| Bassline | 24-36 | Low register, octave 2-3 |
| Chords | 36-50 | Mid-high, octave 3-4 |
| Melody | 36-50 | Same as chords for harmony support |
| Hi-Hats | 42 (fixed) | GM closed hi-hat pitch |

### Tempo Calculation
- BPM = beats per minute
- Quarter note duration = 60 / BPM seconds
- Example: At 120 BPM, each quarter note = 0.5 seconds

---

## Quick Reference Table

| Setting | Default | Typical Range | What it controls |
|---------|---------|---------------|------------------|
| Root Note | C (MIDI 60) | Any MIDI 0-127 | Key of the piece |
| Scale Mode | Major | 8 modes available | Which notes are "in tune" |
| BPM | 120 | 40-300 | Speed/tempo |
| Bars | 8 | 1-64 | Length of generated track |
| Seed | Random (0) | Any integer | Reproducibility control |

---

## Need More Help?

Try these presets:
- **Pop/rock**: C major, 120 BPM, 8 bars
- **Ballad**: A minor, 75 BPM, 16 bars  
- **Jazz**: D dorian, 90 BPM, 8 bars
- **Electronic**: Any key, 140+ BPM, 8 bars

Generate multiple times with different seeds to explore variations!
