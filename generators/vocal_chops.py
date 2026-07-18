"""
Vocal Chops Generator — Monophonic lead synth with 16th-note triplets and syncopation.

Logic:
  - Monophonic (one note at a time) lead synth pattern
  - Heavy use of 16th-note triplets and syncopation
  - Tightly intertwined with main melody: fills gaps between kick (beat 1) and snare (beat 3)
  - Pitch range: octave 5-6 (MIDI 72-96)
  - Uses rapid chromatic approach notes to target tones
  - If mido supports pitch bend, add pitch bend messages for portamento effect
  - Otherwise, use 3-note chromatic approach (e.g., G#-A-A#-B to target B)

Output file: vocal_chops.mid
"""

from typing import List, Tuple
import random
import math

from generators.common import (
    GenerationConfig, get_scale_notes_midi, get_register_range,
    get_velocity_range, generate_midi_file, VOCAL_CHOP_PATTERNS,
    build_chord_progression, get_chord_at_position
)


def generate_vocal_chops(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate a vocal chops / synth fill pattern.

    Creates a monophonic lead pattern with:
    - 16th-note triplets and syncopation
    - Chromatic approach notes to target chord tones
    - Fills the rhythmic gaps between kick (beat 1) and snare (beat 3)

    Args:
        config: Generation configuration

    Returns:
        List of (pitch, duration_seconds, velocity) tuples
    """
    # Seed RNG if provided
    if config.seed is not None:
        random.seed(config.seed)

    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)
    seconds_per_beat = 60.0 / config.bpm
    sixteenth_note = seconds_per_beat * 0.25      # 1/16 note
    triplet_16th = seconds_per_beat * (1.0 / 6.0)  # 1/16 triplet = 1/6 beat

    # Build chord progression for harmonic context
    chord_progression = build_chord_progression(config)

    all_notes: List[Tuple[int, float, int]] = []

    for bar in range(config.bar_length):
        _, chord_notes = get_chord_at_position(bar, 0, chord_progression)
        
        # Determine the rhythmic grid for this bar
        # Kick = beat 1, Snare = beat 3
        # Vocal chops fill the spaces between them
        
        # Beat 1: kick is here — vocal chops are quiet or play a short accent
        # Beat 2: fill space before snare build
        # Beat 3: snare is here — vocal chops answer
        # Beat 4: fill space

        if not chord_notes:
            chord_notes = scale_notes_midi

        # Generate notes for each beat
        for beat in range(4):
            beat_notes = _generate_beat_pattern(
                beat, chord_notes, scale_notes_midi,
                seconds_per_beat, sixteenth_note, triplet_16th, bar
            )
            all_notes.extend(beat_notes)

    return all_notes


def _generate_beat_pattern(
    beat: int,
    chord_notes: List[int],
    scale_notes_midi: List[int],
    seconds_per_beat: float,
    sixteenth_note: float,
    triplet_16th: float,
    bar: int
) -> List[Tuple[int, float, int]]:
    """
    Generate vocal chop pattern for a single beat.

    Beat 0 (kick): short accent or rest
    Beat 1 (space before snare): fast triplet fill
    Beat 2 (snare): quick answering note
    Beat 3 (space after snare): building to next kick
    """
    notes: List[Tuple[int, float, int]] = []

    if beat == 0:
        # Kick beat — short accent or rest
        if random.random() < 0.5:
            # Short accent note
            target = _get_chord_target(chord_notes, scale_notes_midi)
            # Chromatic approach to target
            approach = _chromatic_approach(target, 3, target)
            for p in approach:
                # FORCE register 72-96 (this path was missing clamping!)
                pitch = p
                while pitch < 72:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                notes.append((pitch, triplet_16th, random.randint(60, 90)))

    elif beat == 1:
        # Space before snare — fast triplet fill
        if random.random() < 0.8:
            num_notes = random.choice([3, 4, 5])
            note_dur = seconds_per_beat / num_notes
            pattern_name = random.choice(list(VOCAL_CHOP_PATTERNS.keys()))
            pattern = VOCAL_CHOP_PATTERNS[pattern_name]
            target = _get_chord_target(chord_notes, scale_notes_midi)
            for i in range(num_notes):
                # Apply pattern offset for chromatic approach
                if pattern:
                    offset = pattern[i % len(pattern)]
                else:
                    offset = 0
                pitch = target + offset
                # Snap to nearest scale note
                pitch = _snap_to_scale(pitch, scale_notes_midi)
                # Ensure register 72-96
                while pitch < 72:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                # Accent on first and last
                vel = random.randint(70, 100) if i in (0, num_notes - 1) else random.randint(50, 80)
                notes.append((pitch, note_dur, vel))

    elif beat == 2:
        # Snare beat — answering note
        if random.random() < 0.6:
            target = _get_chord_target(chord_notes, scale_notes_midi)
            # Short rising approach
            approach_len = random.randint(2, 3)
            for i in range(approach_len):
                offset = i  # Step up chromatically
                pitch = target - approach_len + offset
                pitch = _snap_to_scale(pitch, scale_notes_midi)
                while pitch < 72:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                dur = triplet_16th if i < approach_len - 1 else seconds_per_beat * 0.5
                vel = random.randint(65, 95)
                notes.append((pitch, dur, vel))

    elif beat == 3:
        # After snare — building to next kick
        if random.random() < 0.75:
            target = _get_chord_target(chord_notes, scale_notes_midi)
            num_notes = random.choice([2, 3, 4])
            note_dur = seconds_per_beat / num_notes
            # Ascending pattern to create energy
            for i in range(num_notes):
                ascent = int((i / num_notes) * 4)  # Rise up to 4 semitones
                pitch = target + ascent
                pitch = _snap_to_scale(pitch, scale_notes_midi)
                while pitch < 72:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                vel = random.randint(50, 75) + int((i / num_notes) * 30)  # Crescendo
                notes.append((pitch, note_dur, vel))

    return notes


def _get_chord_target(chord_notes: List[int], scale_notes_midi: List[int]) -> int:
    """Get a target pitch from the chord, weighted toward interesting tones."""
    if not chord_notes:
        return random.choice(scale_notes_midi) if scale_notes_midi else 84

    # Weight: prefer 3rd and 5th over root for vocal chops
    if len(chord_notes) >= 3 and random.random() < 0.7:
        return random.choice(chord_notes[1:])  # 3rd or 5th
    return random.choice(chord_notes)


def _chromatic_approach(target: int, num_notes: int, scale_notes: List[int]) -> List[int]:
    """
    Generate a chromatic approach to a target note.
    
    Example: target=84 (C6), num_notes=3 → [81, 82, 83, 84]
    Returns approach notes ascending to the target.
    """
    approach = []
    for i in range(num_notes):
        approach.append(target - num_notes + i)
    approach.append(target)
    return approach


def _snap_to_scale(pitch: int, scale_notes_midi: List[int]) -> int:
    """Snap a pitch to the nearest note in the scale."""
    if not scale_notes_midi:
        return pitch
    if pitch in scale_notes_midi:
        return pitch

    best = pitch
    best_diff = 12
    for scale_note in scale_notes_midi:
        for octave_offset in range(-2, 3):
            candidate = scale_note + (octave_offset * 12)
            diff = abs(pitch - candidate)
            if diff < best_diff:
                best_diff = diff
                best = candidate
    return best


def generate_vocal_chops_progression(config: GenerationConfig,
                                      output_path: str) -> List[Tuple[int, float, int]]:
    """Generate vocal chops and save to MIDI file."""
    notes = generate_vocal_chops(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes