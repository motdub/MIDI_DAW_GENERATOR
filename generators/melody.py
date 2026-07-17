"""
Melody Generator - Generates melodic lines over chord progressions for LMMS import.
Algorithmic, no ML models used. Uses chord-tone-weighted note selection.
"""

from typing import List, Tuple
import random as py_random
from dataclasses import dataclass

from generators.common import (
    GenerationConfig, get_scale_notes, get_chord_from_scale_degree,
    get_midi_note_from_name, get_register_range, generate_midi_file,
    CHORD_PROGRESSIONS, get_scale_notes_midi
)


@dataclass
class MelodyTrackData:
    """Data structure for melody track output."""
    notes: List[Tuple[int, int]]  # [(pitch, duration), ...]
    times: List[float]  # [time, time+duration, ...]


def generate_melody(config: GenerationConfig) -> List[Tuple[int, float]]:
    """
    Generate a melody over the chord progression.

    Uses chord-tone-weighted note selection:
    - Strong beats favor chord tones
    - Weak beats allow scale passing tones

    Includes simple contour rules to avoid large repeated leaps.

    Args:
        config: Generation configuration (key, tempo, bar length)

    Returns:
        List of (pitch, duration_seconds) tuples for each note in the track
    """
    # Get scale notes as MIDI pitches
    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)

    # Determine chord progression type
    prog_name = 'I-V-vi-IV' if not hasattr(config, '_custom_progression') else getattr(
        config, '_custom_progression', None
    ) or 'I-V-vi-IV'

    roman_list = CHORD_PROGRESSIONS[prog_name]

    # Build a mapping of Roman numerals to scale degree indices
    def roman_to_degree_idx(roman: str) -> int:
        mapping = {
            'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4,
            'vi': 5, 'VII': 6,
            'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4,
            'VI': 5,
        }
        return mapping.get(roman, 0)

    # Pre-compute chord tones (root, third, fifth) for each roman numeral
    chord_tones_per_roman: dict = {}
    for roman in set(roman_list):
        degree_idx = roman_to_degree_idx(roman)
        if degree_idx < len(scale_notes_midi):
            root = scale_notes_midi[degree_idx]
        else:
            root = 60

        # Get third and fifth
        third_idx = (degree_idx + 2) % 7
        fifth_idx = (degree_idx + 4) % 7

        third = scale_notes_midi[third_idx] if third_idx < len(scale_notes_midi) else root + 4
        fifth = scale_notes_midi[fifth_idx] if fifth_idx < len(scale_notes_midi) else root + 7

        # Put in a good melodic register (octave 4-5, MIDI 60-84)
        while root < 60:
            root += 12
        while root > 84:
            root -= 12
        while third < root - 12:
            third += 12
        while third >= root + 12:
            third -= 12
        while fifth < third - 12:
            fifth += 12
        while fifth >= third + 12:
            fifth -= 12

        chord_tones_per_roman[roman] = [root, third, fifth]

    seconds_per_beat = 60.0 / config.bpm
    eighth_note_duration = seconds_per_beat * 0.5

    all_notes: List[Tuple[int, float]] = []

    # Track last pitch for contour control
    last_pitch = None

    for bar in range(config.bar_length):
        # Determine chord for this bar
        if bar == 0:
            chord_idx = 0
        elif bar % 4 == 2:
            chord_idx = min(3, len(roman_list) - 1)
        else:
            chord_idx = py_random.randint(0, len(roman_list) - 1)

        roman = roman_list[chord_idx]
        chord_tones = chord_tones_per_roman.get(roman, [60, 64, 67])

        # Generate melody notes for this bar (8 eighth-notes)
        for beat in range(4):
            for eighth in range(2):
                is_strong_beat = (beat == 0 or beat == 2)

                if is_strong_beat:
                    # Strong beat: prefer chord tones (70% chance)
                    if py_random.random() < 0.7 and chord_tones:
                        pitch = py_random.choice(chord_tones)
                    else:
                        pitch = py_random.choice(scale_notes_midi) if scale_notes_midi else 60
                else:
                    # Weak beat: allow scale passing tones (85% chance to stay in scale)
                    if py_random.random() < 0.85:
                        pitch = py_random.choice(scale_notes_midi) if scale_notes_midi else 60
                    else:
                        pitch = py_random.choice(chord_tones) if chord_tones else 60

                # Apply contour rule: avoid leaps > 12 semitones
                if last_pitch is not None and abs(pitch - last_pitch) > 12:
                    # Try a different note closer to the last pitch
                    candidates = [p for p in (chord_tones + scale_notes_midi)
                                  if abs(p - last_pitch) <= 12]
                    if candidates:
                        pitch = py_random.choice(candidates)

                # Keep in melodic register
                while pitch < 60:
                    pitch += 12
                while pitch > 84:
                    pitch -= 12

                all_notes.append((pitch, eighth_note_duration))
                last_pitch = pitch

    return all_notes


def generate_melody_progression(config: GenerationConfig,
                                 output_path: str) -> List[Tuple[int, float]]:
    """Generate melody progression and save to MIDI file."""
    notes = generate_melody(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path, velocity=75)

    return notes


def get_register_range() -> Tuple[int, int]:
    """Get recommended register range for melody."""
    return (60, 84)