"""
Melody Generator — Generates melodic lines over chord progressions for LMMS import.
Enhanced with 8-bar phrase structure, rests, motif development, and stepwise motion.

Algorithmic, no ML models used.
Output file: melody.mid
"""

from typing import List, Tuple, Optional
import random

from generators.common import (
    GenerationConfig, get_scale_notes_midi, generate_midi_file,
    build_chord_progression, get_chord_at_position, roman_to_degree_idx,
    CHORD_PROGRESSIONS
)


def generate_melody(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate a melody over the chord progression with phrase structure.

    Features:
    - 8-bar phrases with distinct "A" part (bars 1-4) and "B" part (bars 5-8)
    - 20-30% rests for breathing room
    - Motif development: repeat first 4-note idea with variation
    - Avoid ending on the root note (creates tension)
    - Stepwise motion more than leaps (limit > 12 semitones)
    - Chord-tone-weighted note selection (strong beats favor chord tones)

    Args:
        config: Generation configuration (key, tempo, bar length)

    Returns:
        List of (pitch, duration_seconds, velocity) tuples
    """
    # Seed RNG if provided
    if config.seed is not None:
        random.seed(config.seed)

    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)
    chord_progression = build_chord_progression(config)

    seconds_per_beat = 60.0 / config.bpm
    eighth_note_duration = seconds_per_beat * 0.5
    quarter_note = seconds_per_beat
    half_note = seconds_per_beat * 2.0

    all_notes: List[Tuple[int, float, int]] = []
    last_pitch: Optional[int] = None

    # Generate an initial motif from the first chord
    motif: List[int] = []
    for bar in range(min(config.bar_length, 8)):
        _, chord_notes = get_chord_at_position(bar, 0, chord_progression)

        if bar == 0:
            # Build motif from first bar's chord tones
            motif = _generate_motif(chord_notes, scale_notes_midi)

        bar_notes, last_pitch = _generate_bar_phrase(
            bar, chord_notes, scale_notes_midi, motif,
            seconds_per_beat, eighth_note_duration, quarter_note, half_note,
            last_pitch, config.bar_length
        )
        all_notes.extend(bar_notes)

    return all_notes


def _generate_motif(chord_notes: List[int],
                    scale_notes_midi: List[int]) -> List[int]:
    """
    Generate a 4-note motif from the chord tones.
    This motif will be developed throughout the melody.
    """
    if not chord_notes:
        chord_notes = [60, 64, 67]

    motif = []
    for i in range(4):
        if i == 0:
            # First note: root or third
            pitch = chord_notes[0] if random.random() < 0.5 else chord_notes[1]
        elif i == 2:
            # Third note: chord tone
            pitch = random.choice(chord_notes)
        else:
            # Passing tones from scale
            candidates = [n for n in scale_notes_midi if 60 <= n <= 84]
            if candidates:
                pitch = random.choice(candidates)
            else:
                pitch = random.choice(chord_notes)

        # Keep in register
        while pitch < 60:
            pitch += 12
        while pitch > 84:
            pitch -= 12

        motif.append(pitch)

    return motif


def _generate_bar_phrase(
    bar: int,
    chord_notes: List[int],
    scale_notes_midi: List[int],
    motif: List[int],
    seconds_per_beat: float,
    eighth_note_duration: float,
    quarter_note: float,
    half_note: float,
    last_pitch: Optional[int],
    total_bars: int
) -> Tuple[List[Tuple[int, float, int]], Optional[int]]:
    """
    Generate a single bar of melody.

    Implements 8-bar phrase structure:
    - Bars 0-3: A part (establish motif)
    - Bars 4-7: B part (develop motif)
    - If total bars < 8, uses simple structure
    """
    notes: List[Tuple[int, float, int]] = []
    bar_in_phrase = bar % 8
    is_a_part = bar_in_phrase < 4
    is_b_part = bar_in_phrase >= 4

    if not chord_notes:
        chord_notes = [60, 64, 67]

    if not scale_notes_midi:
        scale_notes_midi = [60, 62, 64, 65, 67, 69, 71]

    # Determine how many notes in this bar (8th-note grid)
    num_slots = 8  # 8 eighth-notes per bar

    for slot in range(num_slots):
        beat = slot // 2
        is_strong_beat = (beat == 0 or beat == 2)

        # 20-30% rests: skip some slots
        if random.random() < 0.25 and not is_strong_beat:
            # Rest — skip this slot (velocity 0)
            notes.append((60, eighth_note_duration, 0))  # vel=0 = rest
            continue

        # Determine pitch based on phrase section
        if is_a_part:
            # A part: use motif with slight variation
            pitch = _get_motif_note(motif, slot, chord_notes, scale_notes_midi, last_pitch)
        else:
            # B part: develop motif (transpose, invert, fragment)
            pitch = _develop_motif(motif, slot, bar_in_phrase, chord_notes, scale_notes_midi, last_pitch)

        # Ensure in melodic register (octave 5-6)
        while pitch < 60:
            pitch += 12
        while pitch > 84:
            pitch -= 12

        # Apply stepwise motion preference: limit leaps
        if last_pitch is not None and abs(pitch - last_pitch) > 12:
            # Try a closer note
            candidates = [n for n in (chord_notes + scale_notes_midi)
                         if abs(n - last_pitch) <= 8]
            if candidates:
                pitch = random.choice(candidates)

        # Determine duration
        if slot < num_slots - 1:
            # Check if next slot should be continuous (tied)
            if random.random() < 0.15 and is_strong_beat:
                # Hold for 2 slots (quarter note)
                duration = quarter_note
                # Skip next slot
                notes.append((pitch, duration, _get_velocity(slot, is_strong_beat)))
                # Mark next slot as skipped
                notes.append((61, 0, 0))  # dummy rest with 0 duration to maintain grid
            else:
                duration = eighth_note_duration
                notes.append((pitch, duration, _get_velocity(slot, is_strong_beat)))
        else:
            # Last slot: avoid ending on root
            pitch = _avoid_root_on_ending(pitch, chord_notes, scale_notes_midi)
            duration = eighth_note_duration
            notes.append((pitch, duration, _get_velocity(slot, is_strong_beat)))

        last_pitch = pitch

    # Filter out dummy rest entries (0 duration)
    real_notes = [(p, d, v) for p, d, v in notes if d > 0]

    return real_notes, last_pitch


def _get_motif_note(motif: List[int], slot: int,
                    chord_notes: List[int],
                    scale_notes_midi: List[int],
                    last_pitch: Optional[int]) -> int:
    """
    Get a note from the motif or its variation.
    First 4 bars stick close to the motif.
    """
    if motif and slot < len(motif) and random.random() < 0.6:
        # Use motif note directly (with slight octave adjustment)
        pitch = motif[slot]
    elif slot % 2 == 0 and random.random() < 0.7:
        # Strong beat: chord tone
        pitch = random.choice(chord_notes) if chord_notes else 64
    else:
        # Weak beat: scale passing tone
        candidates = [n for n in scale_notes_midi if 60 <= n <= 84]
        pitch = random.choice(candidates) if candidates else 64

    return pitch


def _develop_motif(motif: List[int], slot: int,
                   bar_in_phrase: int,
                   chord_notes: List[int],
                   scale_notes_midi: List[int],
                   last_pitch: Optional[int]) -> int:
    """
    Develop the motif in the B section (bars 4-7).
    Uses transposition, inversion, and fragmentation.
    """
    if not motif:
        return random.choice(chord_notes) if chord_notes else 64

    # Determine development type based on bar position
    dev_type = (bar_in_phrase + slot) % 4

    if dev_type == 0 and slot < len(motif):
        # Transposed motif (up a 3rd or 5th)
        transposition = random.choice([4, 5, 7])  # 3rd, 4th, 5th
        pitch = motif[slot] + transposition
    elif dev_type == 1 and slot < len(motif):
        # Inverted motif (mirror around root)
        root = chord_notes[0] if chord_notes else 60
        inverted = root - (motif[slot] - root)
        pitch = inverted
    elif dev_type == 2:
        # Fragment: use just the first 2 motif notes
        fragment_idx = slot % 2
        if fragment_idx < len(motif):
            pitch = motif[fragment_idx] + random.choice([0, 2, 4])
        else:
            pitch = random.choice(chord_notes) if chord_notes else 64
    else:
        # Free improvisation using chord tones
        pitch = random.choice(chord_notes) if chord_notes else 64

    return pitch


def _avoid_root_on_ending(pitch: int, chord_notes: List[int],
                          scale_notes_midi: List[int]) -> int:
    """
    If the last note would be a root, shift it to a 3rd or 5th instead.
    This creates tension and makes resolution feel more satisfying.
    """
    if chord_notes and pitch == chord_notes[0]:
        # This is a root - replace with 3rd or 5th
        if len(chord_notes) > 2:
            pitch = chord_notes[1]  # 3rd
            if random.random() < 0.5 and len(chord_notes) > 2:
                pitch = chord_notes[2]  # 5th
    elif scale_notes_midi and pitch == scale_notes_midi[0]:
        # Also avoid scale root
        candidates = [n for n in scale_notes_midi if n != pitch]
        if candidates:
            pitch = random.choice(candidates)

    return pitch


def _get_velocity(slot: int, is_strong_beat: bool) -> int:
    """Get a velocity for this note based on its position."""
    base = 75 if is_strong_beat else 60
    variation = random.randint(-10, 15)
    return max(30, min(127, base + variation))


def generate_melody_progression(config: GenerationConfig,
                                 output_path: str) -> List[Tuple[int, float, int]]:
    """Generate melody progression and save to MIDI file."""
    notes = generate_melody(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes