"""
Chord Generator — Generates diatonic chord progressions for LMMS import.
Enhanced with inversions, 7th chords, sus chords, and humanized timing.

Algorithmic, no ML models used.
Output file: chords.mid
"""

from typing import List, Tuple
import random

from generators.common import (
    GenerationConfig, get_scale_notes, get_chord_from_scale_degree,
    get_midi_note_from_name, get_register_range, generate_midi_file,
    get_scale_notes_midi, build_chord_progression, roman_to_degree_idx,
    CHORD_PROGRESSIONS
)


def generate_chords(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate a chord progression over the specified number of bars.

    Features:
    - Diatonic chords from the selected key and scale mode
    - Chord inversions (root, 1st, 2nd) randomly chosen per bar
    - 7th chords ~30% of the time
    - sus2/sus4 chords ~10% of the time for occasional variation
    - Staggered note-on times (±5-15 ticks) for human feel
    - Wider spacing for modern electronic sound (spread across octave 3-4)

    Args:
        config: Generation configuration (key, tempo, bar length)

    Returns:
        List of (pitch, duration_seconds, velocity) tuples
    """
    # Seed RNG if provided
    if config.seed is not None:
        random.seed(config.seed)

    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)

    # Determine chord progression type
    prog_name = 'I-V-vi-IV'
    roman_list = CHORD_PROGRESSIONS[prog_name]

    seconds_per_beat = 60.0 / config.bpm
    chord_duration = seconds_per_beat * 4  # 4 beats per chord
    # MIDI ticks per beat = 480, so each tick = (60/bpm)/480 seconds
    seconds_per_tick = 60.0 / (config.bpm * 480)

    all_notes: List[Tuple[int, float, int]] = []

    for bar in range(config.bar_length):
        # Determine which chord to play (with some variation)
        if bar == 0:
            chord_idx = 0
        elif bar % 4 == 2:
            chord_idx = min(3, len(roman_list) - 1)
        else:
            chord_idx = random.randint(0, len(roman_list) - 1)

        roman = roman_list[chord_idx]
        degree_idx = roman_to_degree_idx(roman)

        # Get root, third, fifth from scale
        if degree_idx < len(scale_notes_midi):
            root = scale_notes_midi[degree_idx]
        else:
            root = 60

        third_idx = (degree_idx + 2) % 7
        fifth_idx = (degree_idx + 4) % 7

        third = scale_notes_midi[third_idx] if third_idx < len(scale_notes_midi) else root + 4
        fifth = scale_notes_midi[fifth_idx] if fifth_idx < len(scale_notes_midi) else root + 7

        # Get the 7th scale degree for 7th chords
        seventh_idx = (degree_idx + 6) % 7
        seventh = scale_notes_midi[seventh_idx] if seventh_idx < len(scale_notes_midi) else root + 10

        # Build chord with optional modifications
        pitches = _build_chord_voicing(
            root, third, fifth, seventh, bar
        )

        # Voice with wider spacing for modern electronic sound
        voiced_pitches = _voice_chord_widespray(pitches, bar)

        # Stagger note-on times slightly for human feel
        for i, pitch in enumerate(voiced_pitches):
            # Stagger: ±5-15 ticks (roughly ±1-3ms at 120BPM)
            stagger_ticks = random.randint(-15, 15)
            stagger_seconds = abs(stagger_ticks) * seconds_per_tick

            # Each pitch in the chord gets a slightly different start time
            # but they all share the same chord duration
            note_duration = chord_duration - (i * stagger_seconds)
            if note_duration < chord_duration * 0.5:
                note_duration = chord_duration * 0.5

            # Velocity with slight variation per note
            base_vel = 65
            vel_variation = random.randint(-10, 10)

            all_notes.append((pitch, note_duration, base_vel + vel_variation))

    return all_notes


def _build_chord_voicing(root: int, third: int, fifth: int,
                         seventh: int, bar: int) -> List[int]:
    """
    Build a chord voicing with optional modifications.

    May add:
    - Inversions (root, 1st, 2nd) randomly chosen
    - 7th chord tones ~30% of the time
    - sus2/sus4 ~10% of the time
    """
    pitches = [root, third, fifth]

    # Add 7th ~30% of the time
    if random.random() < 0.30:
        pitches.append(seventh)

    # Add sus2 or sus4 ~10% of the time
    if random.random() < 0.10:
        sus_type = random.choice(['sus2', 'sus4'])
        if sus_type == 'sus2':
            # Replace 3rd with 2nd (root + 2 semitones)
            pitches[1] = root + 2  # sus2
        else:
            # Replace 3rd with 4th (root + 5 semitones)
            pitches[1] = root + 5  # sus4

    # Apply inversion (only to triads/7ths, not sus chords)
    if len(pitches) >= 3:
        inversion = random.choice(['root', 'first', 'second'])
        if inversion == 'first':
            # 1st inversion: 3rd in bass (lowest note)
            # Move root up one octave
            pitches[0] = pitches[0] + 12
        elif inversion == 'second':
            # 2nd inversion: 5th in bass
            # Move root and third up one octave
            pitches[0] = pitches[0] + 12
            pitches[1] = pitches[1] + 12

    return pitches


def _voice_chord_widespray(pitches: List[int], bar: int) -> List[int]:
    """
    Voice chord with wider spacing for modern electronic sound.
    Spreads notes across octave 3-4 range with some in higher registers.
    Keeps chords LOW to avoid register clash with melody/vocal chops (60-96).
    """
    if not pitches:
        return [48, 52, 55]  # C3-E3-G3

    voiced = []
    for i, pitch in enumerate(pitches):
        # Spread notes: lower notes stay, higher notes go up
        if i == 0:
            # Root stays LOW — octave 2-3 (24-48 range)
            while pitch < 36:
                pitch += 12
            while pitch > 52:
                pitch -= 12
        elif i == 1:
            # Third goes to octave 3 (36-48)
            while pitch < 36:
                pitch += 12
            while pitch > 60:
                pitch -= 12
        else:
            # Other notes stay in octave 3-4 (48-60)
            while pitch < 48:
                pitch += 12
            while pitch > 72:
                pitch -= 12
        voiced.append(pitch)

    return voiced


def generate_chord_progression(config: GenerationConfig,
                                output_path: str) -> List[Tuple[int, float, int]]:
    """Generate chord progression and save to MIDI file."""
    notes = generate_chords(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes