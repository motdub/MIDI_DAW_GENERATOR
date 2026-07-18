"""
Turnaround Fills Generator — Chaotic fills at the end of every 8th bar.

Logic:
  - At the end of every 8th bar (last 2 beats), insert a chaotic fill pattern
  - The fill uses chromatic scale runs: 4-8 notes ascending or descending
  - Pitch bend upward (MIDI pitch bend message) if supported
  - Uses V-chord tones (dominant chord tones) or chromatic approach to next bar's root
  - Main melody should have its last 2 beats of every 8th bar replaced with rests
    (this generator exports a list of (bar, start_beat, duration) for those positions)

Output file: turnaround_fills.mid
"""

from typing import List, Tuple
import random

from generators.common import (
    GenerationConfig, get_scale_notes_midi, get_register_range,
    get_velocity_range, generate_midi_file, build_chord_progression,
    get_chord_at_position
)


# Generate a list of (bar, start_beat, duration_in_bars) indicating where
# the melody should be blanked out for turnaround fills.
# Each entry means: at bar X, from start_beat Y, rest for Z beats.
def get_melody_blank_positions(config: GenerationConfig) -> List[Tuple[int, float, float]]:
    """
    Get the positions where the main melody should be silent.
    
    Every 8th bar, the last 2 beats are blanked out for the turnaround fill.
    
    Returns:
        List of (bar_index, start_beat, duration_beats) tuples
    """
    blank_positions: List[Tuple[int, float, float]] = []
    
    for bar in range(config.bar_length):
        # Every 8th bar, counting from bar 7 (0-indexed: 7, 15, 23, ...)
        if (bar + 1) % 8 == 0:
            # Blank out beats 2-4 (last 2 beats of the bar)
            blank_positions.append((bar, 2.0, 2.0))
    
    return blank_positions


def generate_turnaround_fills(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate turnaround fill patterns at the end of every 8th bar.

    Creates chaotic fills with:
    - Chromatic scale runs (4-8 notes ascending)
    - V-chord tones (dominant chord of the key) or chromatic approach to next bar's root
    - High velocity and energy

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
    sixteenth_note = seconds_per_beat * 0.25

    # Build chord progression for harmonic context
    chord_progression = build_chord_progression(config)

    all_notes: List[Tuple[int, float, int]] = []

    for bar in range(config.bar_length):
        # Only add fills on every 8th bar (0-indexed: 7, 15, 23, ...)
        if (bar + 1) % 8 != 0:
            continue

        # Get the chord at this bar for harmonic context
        _, chord_notes = get_chord_at_position(bar, 0, chord_progression)

        # Determine the next bar's chord root (for the chromatic approach)
        next_bar = (bar + 1) % config.bar_length
        _, next_chord_notes = get_chord_at_position(next_bar, 0, chord_progression)

        # Get the V-chord (dominant) for the current key
        # In major: V = scale degree 4 (index 4)
        # In natural minor: V = scale degree 4 (index 4)
        v_chord_root = scale_notes_midi[4] if len(scale_notes_midi) > 4 else 72
        v_third = scale_notes_midi[(4 + 2) % 7] if len(scale_notes_midi) > 6 else v_chord_root + 4
        v_fifth = scale_notes_midi[(4 + 4) % 7] if len(scale_notes_midi) > 8 else v_chord_root + 7

        # Generate the fill for the last 2 beats of this bar
        fill_notes = _generate_fill_pattern(
            bar, v_chord_root, v_third, v_fifth,
            next_chord_notes, scale_notes_midi,
            seconds_per_beat, sixteenth_note, chord_notes
        )
        all_notes.extend(fill_notes)

    return all_notes


def _generate_fill_pattern(
    bar: int,
    v_root: int,
    v_third: int,
    v_fifth: int,
    next_chord_notes: List[int],
    scale_notes_midi: List[int],
    seconds_per_beat: float,
    sixteenth_note: float,
    current_chord_notes: List[int]
) -> List[Tuple[int, float, int]]:
    """
    Generate a chaotic fill pattern for the last 2 beats of an 8th bar.

    The fill should be:
    - 4-8 chromatic notes ascending or descending
    - Based on V-chord tones or chromatic approach to next bar's root
    - High energy, chaotic feel
    - Register: 72-96 (avoid clashing with melody/chords)
    """
    notes: List[Tuple[int, float, int]] = []

    # Choose a pattern type
    pattern_type = random.choice(['chromatic_up', 'chromatic_down', 'v_arpeggio', 'mixed'])

    # Duration: fill lasts 2 beats
    fill_duration = seconds_per_beat * 2.0

    if pattern_type == 'chromatic_up':
        # Ascending chromatic run: 6-8 notes
        num_notes = random.randint(6, 8)
        note_dur = fill_duration / num_notes

        # Start from the V-chord root raised to high register
        start_pitch = v_root + random.randint(12, 24)  # +1 to +2 octaves
        # Ensure in register 72-96 (HIGH register to avoid clash)
        while start_pitch < 72:
            start_pitch += 12
        while start_pitch > 96:
            start_pitch -= 12

        for i in range(num_notes):
            pitch = start_pitch + i
            if pitch > 96:
                pitch -= 12
            velocity = random.randint(90, 120)
            notes.append((pitch, note_dur, velocity))

    elif pattern_type == 'chromatic_down':
        # Descending chromatic run: 6-8 notes
        num_notes = random.randint(6, 8)
        note_dur = fill_duration / num_notes

        # Start very high and descend
        start_pitch = v_root + random.randint(24, 36)  # +2 to +3 octaves
        while start_pitch > 108:
            start_pitch -= 12
        while start_pitch < 84:
            start_pitch += 12

        for i in range(num_notes):
            pitch = start_pitch - i
            if pitch < 72:
                pitch += 12
            velocity = random.randint(85, 115)
            notes.append((pitch, note_dur, velocity))

    elif pattern_type == 'v_arpeggio':
        # V-chord arpeggio: root-3rd-5th-7th in rapid succession
        v_notes = sorted(set([v_root, v_third, v_fifth, v_root + 7, v_root + 10]))
        num_repeats = random.randint(2, 3)
        note_dur = fill_duration / (len(v_notes) * num_repeats)

        for _ in range(num_repeats):
            for v_pitch in v_notes:
                # Push to high register 72-96
                pitch = v_pitch + 12  # +1 octave minimum
                while pitch < 72:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                velocity = random.randint(80, 110)
                notes.append((pitch, note_dur, velocity))

    else:  # mixed — chaotic combination
        num_notes = random.randint(7, 10)
        note_dur = fill_duration / num_notes

        next_root = next_chord_notes[0] if next_chord_notes else v_root

        for i in range(num_notes):
            if i % 2 == 0:
                offset = (i // 2) * 2
                pitch = next_root + random.randint(12, 24) - 3 + offset
            else:
                pitch = random.choice([v_root, v_third, v_fifth]) + 12

            # Clamp to 72-96
            while pitch < 72:
                pitch += 12
            while pitch > 96:
                pitch -= 12

            if i == 0 or i == num_notes - 1:
                velocity = random.randint(100, 127)
            else:
                velocity = random.randint(70, 105)

            notes.append((pitch, note_dur, velocity))

    return notes


def generate_turnaround_fills_progression(config: GenerationConfig,
                                           output_path: str) -> List[Tuple[int, float, int]]:
    """Generate turnaround fills and save to MIDI file."""
    notes = generate_turnaround_fills(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes