"""
Hi-Hat Generator - Generates rhythmic hi-hat patterns for LMMS import.
Algorithmic, no ML models used. Focus on rhythm and velocity.
"""

from typing import List, Tuple
import random as py_random
from dataclasses import dataclass

from generators.common import (
    GenerationConfig, get_register_range, generate_midi_file
)


@dataclass
class HiHatTrackData:
    """Data structure for hi-hat track output."""
    notes: List[Tuple[int, int]]  # [(pitch, duration), ...]
    times: List[float]  # [time, time+duration, ...]


def generate_hihats(config: GenerationConfig) -> List[Tuple[int, float]]:
    """
    Generate a hi-hat rhythm pattern.

    Uses steady 8th/16th notes with probabilistic accents and velocity variation.
    Includes occasional syncopation for groove.

    Args:
        config: Generation configuration (tempo only needed)

    Returns:
        List of (pitch, duration_seconds) tuples for each note in the track
    """
    # GM hi-hat pitches
    HI_HAT_CLOSED = 42
    HI_HAT_OPEN = 46

    seconds_per_beat = 60.0 / config.bpm
    eighth_note = seconds_per_beat * 0.5
    sixteenth_note = seconds_per_beat * 0.25

    all_notes: List[Tuple[int, float]] = []

    for bar in range(config.bar_length):
        for beat in range(4):
            # Play on downbeats (beat 0 and 2) as steady 8th notes
            # Add 16th-note syncopation occasionally
            for subdivision in range(2):  # 2 eighth-notes per beat
                is_strong = (beat == 0 or beat == 2) and subdivision == 0

                if is_strong:
                    # Always play on strong beats
                    pitch = HI_HAT_CLOSED
                    duration = eighth_note
                    all_notes.append((pitch, duration))
                elif py_random.random() < 0.85:
                    # Play most weak 8th notes
                    pitch = HI_HAT_CLOSED
                    duration = eighth_note
                    all_notes.append((pitch, duration))

                # Occasional 16th-note ghost notes
                if py_random.random() < 0.1 and not is_strong:
                    pitch = HI_HAT_CLOSED
                    duration = sixteenth_note
                    all_notes.append((pitch, duration))

                # Occasional open hat on weak beats
                if py_random.random() < 0.05 and beat in (1, 3):
                    pitch = HI_HAT_OPEN
                    duration = eighth_note * 2  # open hat rings longer
                    all_notes.append((pitch, duration))

    return all_notes


def generate_hihat_pattern(config: GenerationConfig,
                            output_path: str) -> List[Tuple[int, float]]:
    """Generate hi-hat pattern and save to MIDI file."""
    notes = generate_hihats(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path, velocity=90)

    return notes


def get_register_range() -> Tuple[int, int]:
    """Get recommended register range for hi-hats."""
    return (42, 46)