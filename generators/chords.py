"""
Chord Generator - Generates diatonic chord progressions for LMMS import.
Algorithmic, no ML models used.
"""

from typing import List, Tuple
import random
from dataclasses import dataclass

from generators.common import (
    GenerationConfig, get_scale_notes, get_chord_from_scale_degree,
    get_midi_note_from_name, get_register_range, generate_midi_file,
    CHORD_PROGRESSIONS, get_scale_notes_midi
)


@dataclass
class ChordTrackData:
    """Data structure for chord track output."""
    notes: List[Tuple[int, int]]  # [(pitch, duration), ...]
    times: List[float]  # [time, time+duration, ...]


def generate_chords(config: GenerationConfig) -> List[Tuple[int, float]]:
    """
    Generate a chord progression over the specified number of bars.

    Uses diatonic chords from the selected key and scale mode.
    Applies common chord progression templates with some variation.

    Args:
        config: Generation configuration (key, tempo, bar length)

    Returns:
        List of (pitch, duration_seconds) tuples for each note in the track
    """
    # Get scale notes for proper chord selection
    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)

    # Determine chord progression type
    prog_name = 'I-V-vi-IV' if not hasattr(config, '_custom_progression') else getattr(
        config, '_custom_progression', None
    ) or 'I-V-vi-IV'

    roman_list = CHORD_PROGRESSIONS[prog_name]

    # Build a mapping of Roman numerals to scale degree indices
    # I=0, II=1, III=2, IV=3, V=4, vi=5, VII=6
    def roman_to_degree_idx(roman: str) -> int:
        mapping = {
            'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4,
            'vi': 5, 'VII': 6,
            'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4,
            'VI': 5,
        }
        return mapping.get(roman, 0)

    # Convert the progression into actual chord tone MIDI pitches
    # Each chord = root, third, fifth from the scale
    chord_pitches = []
    for roman in roman_list:
        degree_idx = roman_to_degree_idx(roman)
        if degree_idx < len(scale_notes_midi):
            root = scale_notes_midi[degree_idx]
        else:
            root = 60  # fallback

        # Get third and fifth from scale
        third_idx = (degree_idx + 2) % 7
        fifth_idx = (degree_idx + 4) % 7

        third = scale_notes_midi[third_idx] if third_idx < len(scale_notes_midi) else root + 4
        fifth = scale_notes_midi[fifth_idx] if fifth_idx < len(scale_notes_midi) else root + 7

        # Voice the chord in a good register (octave 3-4, around MIDI 48-72)
        # Transpose root to comfortable range
        while root < 48:
            root += 12
        while root > 72:
            root -= 12
        while third < root - 12:
            third += 12
        while third >= root + 12:
            third -= 12
        while fifth < third - 12:
            fifth += 12
        while fifth >= third + 12:
            fifth -= 12

        chord_pitches.append([root, third, fifth])

    # Duration per chord change: each chord lasts 4 beats (1 bar)
    # 1 beat = 60/bpm seconds
    seconds_per_beat = 60.0 / config.bpm
    chord_duration = seconds_per_beat * 4  # 4 beats per chord

    all_notes: List[Tuple[int, float]] = []

    for bar in range(config.bar_length):
        # Determine which chord to play (with some variation)
        if bar == 0:
            chord_idx = 0
        elif bar % 4 == 2:
            chord_idx = min(3, len(chord_pitches) - 1)
        else:
            chord_idx = random.randint(0, len(chord_pitches) - 1)

        pitches = chord_pitches[chord_idx]

        # Play the chord as a block — all 3 notes sound simultaneously
        for pitch in pitches:
            all_notes.append((pitch, chord_duration))

    return all_notes


def get_chord_pitch(chord_name: str, root_note: str) -> int:
    """Get the pitch (MIDI note number) for a chord's root."""
    # Parse the chord name to extract the root note
    parts = chord_name.split()
    if len(parts) >= 1:
        return get_midi_note_from_name(parts[0])
    return 60  # Default to C


def generate_chord_progression(config: GenerationConfig,
                                output_path: str) -> List[Tuple[int, float]]:
    """Generate chord progression and save to MIDI file."""
    notes = generate_chords(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path, velocity=70)

    return notes


def get_register_range() -> Tuple[int, int]:
    """Get recommended register range for chords."""
    return (36, 50)