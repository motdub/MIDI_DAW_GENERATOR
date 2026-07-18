# Progress

## ✅ Bug Fixes Applied

### Bug Fix #1 — Fit Score False Negatives
The fit checker was producing **false negatives** — flagging perfectly correct C major bassline notes (like pitch 36 = C2) as "out of scale" because it was comparing against a single-octave list [60, 62, ... 71] instead of checking pitch class.

**Fix**: Rewrote `check_key_conformity()` in `analysis/fit_checker.py`:
- Now uses `pitch % 12` (pitch class) matching via `build_scale_semitone_set()`
- All octaves are correctly recognized
- Chromatic tracks (vocal chops, turnaround fills, counter-melody) get more lenient checking
- Removed the "Major out-of-scale cluster" false positive spam

### Bug Fix #2 — Register Overcrowding
Multiple generators were sharing the same octave range (60-84), causing muddy overlap.

**Fixes applied**:
- **`generators/chords.py`**: Lowered root to 36-52, third to 36-60, upper voices to 48-72 (was 48-84)
- **`generators/vocal_chops.py`**: Added missing register clamping on beat 0 chromatic approach path — force all notes to 72-96
- **`generators/counter_melody.py`**: `_snap_to_scale()` now enforces 72-96 minimum
- **`generators/turnaround_fills.py`**: All fill patterns pushed to 72-96 register (was 60-84 overlapping with chords/melody)

### Bug Fix #3 — MIDI Files Truncated to One Chord (July 17, 2026)
`generate_midi_file()` in `generators/common.py` had a fundamental flaw: the `current_tick` variable was initialized to 0 and **never updated** during the note-collection loop. As a result, all note-off events were scheduled at the same tick offset (= duration_ticks), causing the note-off processing to emit a single tick group and then hit `end_of_track` immediately. A 16-bar song was squashed into ~4 beats.

**Root cause**: The function attempted a two-pass approach (collect all note-offs, then emit them sorted), but `off_tick = current_tick + duration_ticks` always computed `0 + duration_ticks` because `current_tick` was never incremented.

**Fix**: Replaced with a single-pass, chord-block grouping approach:
- Walk the flat note list and group notes with matching durations into chord blocks (within 50-tick tolerance)
- For each chord block: emit all note_ons at time=0, then all note_offs with first note_off advancing the clock by the chord duration and remaining at time=0
- Each chord block naturally advances the track clock, producing correct multi-bar timelines
- No manual `current_tick` tracking needed — MIDI delta times do the work

### Expected Register Separation After Fixes
- Bassline: 24-48 (correct — no overlap)
- Chords: 36-60 (lowered — no overlap with melody)
- Melody: 60-84 (correct)
- Counter-Melody: 72-96 (correct — now enforced)
- Vocal Chops: 72-96 (correct — now enforced)
- Turnaround Fills: 72-96 (correct — now high register)
- Hi-Hats: 42-46 (correct — percussion)
