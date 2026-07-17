"""
Bassline Generator - Generates rhythmic basslines from chord progressions.
Algorithmic, no ML models used.
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
class BasslineTrackData:
    """Data structure for bassline track output."""
    notes: List[Tuple[int, int]]  # [(pitch, duration), ...]
    times: List[float]  # [time, time+duration, ...]


def generate_bassline(config: GenerationConfig) -> List[Tuple[int, float]]:
    """
    Generate a bassline from the chord progression.

    Derives notes from chord roots and fifths with rhythmic variation.
    Root on downbeats, passing/approach tones on weak beats.

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

    # Pre-compute chord roots for the progression
    chord_roots = []
    for roman in roman_list:
        degree_idx = roman_to_degree_idx(roman)
        if degree_idx < len(scale_notes_midi):
            root = scale_notes_midi[degree_idx]
        else:
            root = 60
        # Put bass in low register (octave 2-3, MIDI 24-48)
        while root > 48:
            root -= 12
        while root < 24:
            root += 12
        chord_roots.append(root)

    seconds_per_beat = 60.0 / config.bpm

    all_notes: List[Tuple[int, float]] = []

    for bar in range(config.bar_length):
        # Determine chord index for this bar
        if bar == 0:
            chord_idx = 0
        elif bar % 4 == 2:
            chord_idx = min(3, len(chord_roots) - 1)
        else:
            chord_idx = py_random.randint(0, len(chord_roots) - 1)

        root = chord_roots[chord_idx]
        fifth = root + 7  # perfect fifth above root

        # Apply bass register constraint
        while fifth > 48:
            fifth -= 12

        # Generate bassline notes for this bar (4 beats, 1/8th note resolution)
        for beat in range(4):
            if beat == 0:
                # Downbeat: always play the root
                pitch = root
                duration = seconds_per_beat * 0.5  # 1/8th note
            elif beat == 2:
                # Weak beat: sometimes fifth, sometimes root
                if py_random.random() < 0.5:
                    pitch = fifth
                else:
                    pitch = root
                duration = seconds_per_beat * 0.5
            else:
                # Other beats: passing tone from scale
                pitch = get_bassline_note(root, scale_notes_midi)
                duration = seconds_per_beat * 0.5

            all_notes.append((pitch, duration))

    return all_notes


def get_bassline_note(root_pitch: int, scale_notes_midi: List[int]) -> int:
    """
    Get a bassline note that works with the root pitch.

    Uses passing tones or approach notes from the scale.
    """
    if not scale_notes_midi:
        return root_pitch

    # Try to find a note from the scale that's close to root_pitch
    # and in the bass register (24-48)
    candidates = [n for n in scale_notes_midi if 24 <= n <= 48]

    if candidates:
        return py_random.choice(candidates)

    # Fallback: use the fifth
    fifth = root_pitch + 7
    while fifth > 48:
        fifth -= 12
    return fifth


def generate_bassline_progression(config: GenerationConfig,
                                   output_path: str) -> List[Tuple[int, float]]:
    """Generate bassline progression and save to MIDI file."""
    notes = generate_bassline(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path, velocity=85)

    return notes


def get_register_range() -> Tuple[int, int]:
    """Get recommended register range for bassline."""
    return (24, 36)