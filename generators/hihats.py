"""
Hi-Hat Generator — Generates rhythmic hi-hat patterns for LMMS import.
Enhanced with open hat patterns, crash cymbal, 32nd-note rolls, and wide velocity range.

Algorithmic, no ML models used.
Output file: hihats.mid
"""

from typing import List, Tuple
import random

from generators.common import (
    GenerationConfig, generate_midi_file
)


def generate_hihats(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate a hi-hat rhythm pattern with groove and variety.

    GM Percussion notes:
    - 42 = Closed Hi-Hat
    - 46 = Open Hi-Hat
    - 49 = Crash Cymbal 1

    Features:
    - Steady 8th/16th with probabilistic accents and velocity variation
    - Open hat patterns on off-beats for groove
    - Crash cymbal on first beat of every 4th bar
    - Occasional 32nd-note rolls for buildups
    - Velocity range 20-127

    Args:
        config: Generation configuration (tempo only needed)

    Returns:
        List of (pitch, duration_seconds, velocity) tuples
    """
    # Seed RNG if provided
    if config.seed is not None:
        random.seed(config.seed)

    HI_HAT_CLOSED = 42
    HI_HAT_OPEN = 46
    CRASH = 49

    seconds_per_beat = 60.0 / config.bpm
    eighth_note = seconds_per_beat * 0.5
    sixteenth_note = seconds_per_beat * 0.25
    thirty_second_note = seconds_per_beat * 0.125
    half_note = seconds_per_beat * 2.0

    all_notes: List[Tuple[int, float, int]] = []

    for bar in range(config.bar_length):
        # Crash cymbal on first beat of every 4th bar
        if bar % 4 == 0:
            crash_vel = random.randint(90, 120)
            all_notes.append((CRASH, half_note, crash_vel))

        # Determine if this bar has a 32nd-note roll (20% chance)
        has_32nd_roll = random.random() < 0.20

        for beat in range(4):
            # Primary 8th-note grid
            for eighth in range(2):  # 2 eighth-notes per beat
                is_downbeat = (beat == 0 or beat == 2) and eighth == 0

                if eighth == 0:
                    # First eighth of the beat
                    if is_downbeat:
                        # Strong downbeat: always play closed hat
                        vel = random.randint(60, 100)
                        all_notes.append((HI_HAT_CLOSED, eighth_note, vel))
                    else:
                        # Weak downbeat: play closed hat with high probability
                        if random.random() < 0.90:
                            vel = random.randint(40, 85)
                            all_notes.append((HI_HAT_CLOSED, eighth_note, vel))

                else:  # eighth == 1 — off-beat
                    # Open hat on off-beats for groove (30% chance)
                    if random.random() < 0.30:
                        vel = random.randint(40, 90)
                        all_notes.append((HI_HAT_OPEN, sixteenth_note * 3, vel))
                    else:
                        # Closed hat on off-beat
                        if random.random() < 0.70:
                            vel = random.randint(30, 75)
                            all_notes.append((HI_HAT_CLOSED, eighth_note, vel))

                # 16th-note ghost notes (quick, quiet)
                if random.random() < 0.15 and not is_downbeat:
                    vel = random.randint(20, 50)
                    all_notes.append((HI_HAT_CLOSED, sixteenth_note, vel))

            # 32nd-note roll section (on beat 3 or 4)
            if has_32nd_roll and beat >= 2:
                # Add a tight roll of 4-6 32nd notes
                num_roll_notes = random.choice([4, 5, 6])
                for i in range(num_roll_notes):
                    # Crescendo through the roll
                    roll_vel = 30 + int((i / num_roll_notes) * 60)
                    all_notes.append((HI_HAT_CLOSED, thirty_second_note, roll_vel))

    return all_notes


def generate_hihat_pattern(config: GenerationConfig,
                            output_path: str) -> List[Tuple[int, float, int]]:
    """Generate hi-hat pattern and save to MIDI file."""
    notes = generate_hihats(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes