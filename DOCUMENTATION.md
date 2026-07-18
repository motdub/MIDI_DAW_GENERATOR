# MIDI Track Generator v2 - User Guide

## Quick Start
1. Run `py main.py` to launch the application
2. Check the tracks you want to generate (all OFF by default)
3. Adjust settings and click **"Generate All Enabled"**
4. Wait for the fit score to appear
5. Click **"Open Output Folder"** to view your MIDI files
6. If you don't like the result, click **"Regenerate All"**

---

## Understanding Music Terms

### Root Note
- The **root note** is the tonal center or "home" of your music
- Now selectable by **note name** (C, C#, D, ...) instead of MIDI number
- Common roots: C (bright), G (warm), D (bright minor), A (standard)

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
| **Aeolian** | Same as natural minor | C D E♭ F G A♭ B♭ | Standard minor key |
| **Ionian** | Same as major | C D E F G A B | Major key alternative |

### BPM (Beats Per Minute)
- Controls the **tempo** or speed
- **128 BPM** = default, good for electronic
- **60-80 BPM** = slow ballads
- **140+ BPM** = fast trance/drum & bass

### Bars (Measures)
- **8 bars** = short loop / intro
- **16 bars** = standard verse/chorus
- **32 bars** = full song structure

---

## Track Types Explained

### Chords (chords.mid)
- **Harmonic backing** — the chord progression
- Features: inversions (root/1st/2nd), 7th chords (30%), sus chords (10%)
- Humanized timing with staggered note-ons (±5-15 ticks)
- Voice: Octave 2-4, wide voicing for modern sound

### Bassline (bassline.mid)
- **Rhythmic bass pattern** that locks with chord changes
- 4 pattern types: syncopated 8ths, walking bass, 16th-note groove, syncopated off-beat
- Ghost notes (velocity 20-40) for groove
- Sometimes skips the downbeat for syncopation
- Voice: Low register (MIDI 24-48, octave 2-3)

### Hi-Hats (hihats.mid)
- **Rhythmic percussion** using GM drum notes (42=closed, 46=open, 49=crash)
- Open hat patterns on off-beats for groove
- Crash cymbal on first beat of every 4th bar
- 32nd-note rolls (crescendo) for buildups
- Wide velocity range: 20-127

### Melody (melody.mid)
- **Lead melody** over the chord progression
- 8-bar phrase structure: A part (bars 1-4) + B part (bars 5-8)
- A part: establishes a 4-note motif
- B part: develops the motif via transposition, inversion, and fragmentation
- 20-30% rests for breathing room
- Avoids ending on the root note (creates tension)
- Voice: MIDI 60-84 (octave 5-6)

### Counter-Melody (counter_melody.mid) ⬅️ NEW
- **Call-and-answer response** to the main melody
- When the main melody rests or holds a long note (>2 beats), counter-melody fills the gap
- Call-and-answer structure: melody = "call" (beats 1-2), counter = "answer" (beats 3-4)
- Fast 4-6 note phrases using arpeggio and scale-run patterns
- Voice: High register (MIDI 72-96), one octave above melody

### Vocal Chops (vocal_chops.mid) ⬅️ NEW
- **Monophonic lead synth** with rapid chromatic runs
- Beat-grid-aware: fills space between kick (beat 1) and snare (beat 3)
- Uses chromatic approach runs (e.g., G#-A-A#-B to target B)
- 16th-note triplets and syncopation
- Prefers 3rd and 5th of the chord over root
- Voice: MIDI 72-96 (octave 5-6)

### Turnaround Fills (turnaround_fills.mid) ⬅️ NEW
- **Chaotic fills** at the end of every 8th bar (last 2 beats)
- 4 pattern types: ascending/descending chromatic runs, V-chord arpeggios, mixed chaotic
- Creates anticipation for the next phrase
- High velocity (90-127) for impact
- Voice: MIDI 72-96 (high register, avoid clashing)

---

## Cross-Track Coordination

The generators work together as an ensemble:

| Rule | How it works |
|------|-------------|
| **Call-and-answer** | Counter-melody only plays when melody rests or holds long notes |
| **Register stacking** | Each track has a dedicated octave range (see table below) |
| **Chord grounding** | All tracks derive from the same chord progression |
| **Bar-end rest** | Turnaround fills blank out the melody on beat 4 of every 8th bar |

### Register Allocation

| Track | MIDI Range | Octave |
|-------|-----------|--------|
| Bassline | 24-48 | 2-3 |
| Hi-Hats | 42-46 | percussion |
| Chords | 36-60 | 3-4 |
| Melody | 60-84 | 5-6 |
| Counter-Melody | 72-96 | 6-7 |
| Vocal Chops | 72-96 | 6-7 |
| Turnaround Fills | 72-96 | 6-7 |

---

## Seed Control

### What is a seed?
A **seed** controls randomness. Same seed + same settings = same output.

### How to use:
1. Click **"Randomize Seed"** for a new random value
2. Or type any number (0 to 2,147,483,647)
3. The seed affects ALL tracks simultaneously

---

## Track Enable/Disable

All tracks are **OFF by default**. Check the ones you want:

| Track | Default | When to enable |
|-------|---------|----------------|
| Bassline | OFF | For bass-driven tracks |
| Chords | OFF | Essential for harmonic foundation |
| Hi-Hats | OFF | For percussion |
| Melody | OFF | For lead lines |
| Counter-Melody | OFF | For call-and-answer fills |
| Vocal Chops | OFF | For Monstercat-style vocal fills |
| Turnaround Fills | OFF | For bar-end transitions |

---

## Per-Track Controls

Each track has 4 sliders:

| Slider | Range | What it does |
|--------|-------|-------------|
| **Vel Min** | 0-127 | Softest note velocity |
| **Vel Max** | 0-127 | Loudest note velocity |
| **Octave** | -2 to +2 | Transpose entire track |
| **Complexity** | 0-100% | More notes = more complex |

---

## Fit Checker & Score

After generation, the fit checker analyzes all tracks and shows a **score out of 100**:

| Score | Color | Meaning |
|-------|-------|---------|
| 80-100 | 🟢 Green | Excellent — well-coordinated |
| 60-79 | 🟡 Yellow | Good — minor issues |
| < 60 | 🔴 Red | Needs improvement — regenerate |

The score considers:
- **Key conformity** — notes match the selected scale (octave-correct)
- **Harmonic clashes** — no dissonant intervals between tracks
- **Call-and-answer** — counter-melody doesn't overlap melody
- **Register separation** — tracks don't crowd the same octave
- **Syncopation density** — vocal chops have enough off-beat notes
- **Rhythmic alignment** — bass lands on chord changes

---

## Output Files

### Files created:
- `bassline.mid`
- `chords.mid`
- `hihats.mid`
- `melody.mid`
- `counter_melody.mid`
- `vocal_chops.mid`
- `turnaround_fills.mid`

Each is a **MIDI Type 1** file importable into LMMS, Ableton Live, FL Studio, etc.

### Naming scheme:
The `counter_melody.mid` file uses lowercase with underscores matching the GUI track name "Counter-Melody".

---

## Example Workflows

### Monstercat-style Future Bass
- Root Note: **G** or **A**
- Scale: **Major** or **Mixolydian**
- BPM: **140-150**
- Bars: **16** (verse + drop)
- Enable: All 7 tracks
- Keeps: Counter-melody for call-and-answer, vocal chops for fills

### Minimal Deep House
- Root Note: **D** or **E**
- Scale: **Dorian**
- BPM: **120-126**
- Bars: **8** (loop)
- Enable: Bassline, Chords, Hi-Hats, Vocal Chops
- Keep complexity low (30-50%) on all tracks

### Cinematic / Ambient
- Root Note: **A** or **C**
- Scale: **Natural Minor** or **Lydian**
- BPM: **70-90**
- Bars: **16**
- Enable: Chords, Melody, Counter-Melody
- Keep melody complexity moderate (50%) for breathing room

---

## Troubleshooting

### Fit score is low (< 60)
- Click **"Regenerate All"** for a different random roll
- Try a different seed
- Fewer tracks = less register overlap = higher score

### Files won't import into my DAW
- All files are standard MIDI Type 1
- Import each file as a separate track
- LMMS: File → Import → MIDI File

---

## Quick Reference Table

| Setting | Default | Range | What it controls |
|---------|---------|-------|------------------|
| Root Note | C | C, C#, D, ..., B | Key of the piece |
| Scale Mode | Major | 8 modes | Which notes are "in tune" |
| BPM | 128 | 40-300 | Speed/tempo |
| Bars | 16 | 1-64 | Length of generated track |
| Seed | 0 | Any integer | Reproducibility |

---

© 2026 motdub All rights reserved.