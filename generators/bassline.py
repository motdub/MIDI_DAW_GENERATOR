"""
Bassline Generator — Generates rhythmic, syncopated basslines from chord progressions.
Enhanced with 8th/16th note patterns, ghost notes, walking bass, and syncopation.

Algorithmic, no ML models used.
Output file: bassline.mid
"""

from typing import List, Tuple
import random

from generators.common import (
    GenerationConfig, get_scale_notes_midi, generate_midi_file,
    build_chord_progression, get_chord_at_position, roman_to_degree_idx,
    CHORD_PROGRESSIONS
)


def generate_bassline(config: GenerationConfig) -> List[Tuple[int, float, int]]:
    """
    Generate a bassline from the chord progression with rhythmic variety.

    Features:
    - 8th-note and 16th-note patterns based on the chord being played
    - Occasional ghost notes (very low velocity, 20-40)
    - Syncopation: sometimes skip the downbeat, hit the 'and' of 1 instead
    - Walking bass patterns between chord roots
    - Still in low register (MIDI 24-48, octave 2-3)

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

    all_notes: List[Tuple[int, float, int]] = []

    # Keep track of the last root for walking bass transitions
    last_root = 36  # C2 default low

    for bar in range(config.bar_length):
        _, chord_notes = get_chord_at_position(bar, 0, chord_progression)

        if not chord_notes:
            chord_notes = scale_notes_midi

        root = chord_notes[0]
        # Put in bass register (octave 2-3, MIDI 24-48)
        while root > 48:
            root -= 12
        while root < 24:
            root += 12

        fifth = chord_notes[2] if len(chord_notes) > 2 else root + 7
        while fifth > 48:
            fifth -= 12
        while fifth < 24:
            fifth += 12

        third = chord_notes[1] if len(chord_notes) > 1 else root + 4
        while third > 48:
            third -= 12
        while third < 24:
            third += 12

        # Generate bar pattern
        bar_notes = _generate_bar_pattern(
            bar, root, third, fifth, last_root, scale_notes_midi,
            seconds_per_beat
        )
        all_notes.extend(bar_notes)

        last_root = root

    return all_notes


def _generate_bar_pattern(
    bar: int,
    root: int,
    third: int,
    fifth: int,
    last_root: int,
    scale_notes_midi: List[int],
    seconds_per_beat: float
) -> List[Tuple[int, float, int]]:
    """
    Generate a single bar of bassline with rhythmic variety.

    Each bar has 4 beats, subdivided into 8th or 16th notes.
    """
    notes: List[Tuple[int, float, int]] = []

    # Choose a pattern for this bar
    pattern_choice = random.random()

    if pattern_choice < 0.25:
        # Pattern 1: Simple 8th-note root pattern with syncopation
        notes = _pattern_syncopated_eighths(root, third, fifth, seconds_per_beat)
    elif pattern_choice < 0.50:
        # Pattern 2: Walking bass with octave jumps
        notes = _pattern_walking_bass(root, third, fifth, last_root, scale_notes_midi, seconds_per_beat)
    elif pattern_choice < 0.75:
        # Pattern 3: 16th-note grooves with ghost notes
        notes = _pattern_sixteenth_groove(root, third, fifth, seconds_per_beat)
    else:
        # Pattern 4: Syncopated off-beat pattern
        notes = _pattern_syncopated_offbeat(root, third, fifth, seconds_per_beat)

    return notes


def _pattern_syncopated_eighths(
    root: int,
    third: int,
    fifth: int,
    seconds_per_beat: float
) -> List[Tuple[int, float, int]]:
    """
    Simple 8th-note pattern with occasional syncopation.
    Sometimes skips the downbeat and hits the 'and' of 1 instead.
    """
    notes: List[Tuple[int, float, int]] = []
    eighth_dur = seconds_per_beat * 0.5

    # Decide whether to play on downbeat (beat 0) or skip it
    play_downbeat = random.random() < 0.7  # 70% chance to play downbeat

    for eighth in range(8):  # 8 eighth-notes per bar
        beat = eighth // 2
        is_downbeat = (eighth % 2 == 0)

        if eighth == 0 and not play_downbeat:
            # Skip the downbeat — hit the 'and' of 1 instead
            continue
        elif eighth == 1 and not play_downbeat:
            # Play on the 'and' of 1
            pitch = root
            vel = random.randint(70, 90)
            notes.append((pitch, eighth_dur, vel))
            continue

        # Normal pattern
        if is_downbeat:
            # Root on downbeats (beats 0, 2)
            if beat in (0, 2):
                pitch = root
                vel = random.randint(75, 95)
            else:
                # Beats 1, 3: alternate between fifth and root
                pitch = fifth if random.random() < 0.5 else root
                vel = random.randint(60, 80)
            notes.append((pitch, eighth_dur, vel))
        else:
            # Off-beat: passing tone or ghost note
            if random.random() < 0.3:
                # Ghost note — very low velocity
                pitch = root
                vel = random.randint(20, 40)
                dur = eighth_dur * 0.5  # Shorter
                notes.append((pitch, dur, vel))
            elif random.random() < 0.5:
                # Connect to next chord root via scale tone
                pitch = _get_walking_note(root, last_root=root, scale_notes_midi=[root, third, fifth])
                vel = random.randint(50, 70)
                notes.append((pitch, eighth_dur, vel))

    return notes


def _pattern_walking_bass(
    root: int,
    third: int,
    fifth: int,
    last_root: int,
    scale_notes_midi: List[int],
    seconds_per_beat: float
) -> List[Tuple[int, float, int]]:
    """
    Walking bass pattern that steps between chord roots.
    Uses scale tones to create a smooth line between changes.
    """
    notes: List[Tuple[int, float, int]] = []
    eighth_dur = seconds_per_beat * 0.5

    # Walking bass: root on beat 1, then stepwise motion through the bar
    for beat in range(4):
        if beat == 0:
            # Beat 1: hit the root
            notes.append((root, eighth_dur, random.randint(75, 95)))
            notes.append((root, eighth_dur, random.randint(60, 80)))
        elif beat == 1:
            # Beat 2: approach note (chromatic or scale step)
            approach = _get_walking_note(root, last_root, scale_notes_midi)
            notes.append((approach, eighth_dur, random.randint(55, 75)))
            notes.append((approach, eighth_dur, random.randint(50, 70)))
        elif beat == 2:
            # Beat 3: fifth or third
            pitch = fifth if random.random() < 0.6 else third
            notes.append((pitch, eighth_dur, random.randint(65, 85)))
            notes.append((pitch, eighth_dur, random.randint(55, 75)))
        else:
            # Beat 4: walk back toward the next root
            # Try to come within a 5th of the root for resolution
            if random.random() < 0.5:
                pitch = root - 5  # A 4th below
            else:
                pitch = _get_walking_note(root, last_root, scale_notes_midi)
            while pitch > 48:
                pitch -= 12
            while pitch < 24:
                pitch += 12
            notes.append((pitch, eighth_dur, random.randint(60, 80)))
            notes.append((pitch, eighth_dur, random.randint(50, 70)))

    return notes


def _pattern_sixteenth_groove(
    root: int,
    third: int,
    fifth: int,
    seconds_per_beat: float
) -> List[Tuple[int, float, int]]:
    """
    16th-note groove pattern with ghost notes.
    Root on beats 1 and 3, with faster subdivisions in between.
    """
    notes: List[Tuple[int, float, int]] = []
    sixteenth_dur = seconds_per_beat * 0.25

    for sixteenth in range(16):  # 16 sixteenth-notes per bar
        beat = sixteenth // 4
        position_in_beat = sixteenth % 4

        # Decide what to play based on position
        if position_in_beat == 0:
            # Downbeat of each quarter note
            if beat in (0, 2):
                # Strong beat: hit the root
                vel = random.randint(75, 95)
                notes.append((root, sixteenth_dur * 2, vel))
            else:
                # Weak beats (1, 3): alternate
                pitch = third if random.random() < 0.5 else fifth
                vel = random.randint(60, 80)
                notes.append((pitch, sixteenth_dur * 1.5, vel))

        elif position_in_beat == 2:
            # 'And' of the beat: ghost note or passing tone
            if random.random() < 0.4:
                # Ghost note
                notes.append((root, sixteenth_dur, random.randint(20, 40)))
            elif random.random() < 0.5:
                # Accented passing tone
                pitch = _get_walking_note(root, root, [root, third, fifth])
                vel = random.randint(40, 60)
                notes.append((pitch, sixteenth_dur, vel))

    return notes


def _pattern_syncopated_offbeat(
    root: int,
    third: int,
    fifth: int,
    seconds_per_beat: float
) -> List[Tuple[int, float, int]]:
    """
    Syncopated off-beat pattern: hits on the 'and' of beats,
    creating a funky, driving feel.
    """
    notes: List[Tuple[int, float, int]] = []
    eighth_dur = seconds_per_beat * 0.5

    for eighth in range(8):
        is_downbeat = (eighth % 2 == 0)

        if is_downbeat:
            # Downbeats: mostly rests, occasional ghost notes
            if random.random() < 0.2:
                vel = random.randint(20, 40)
                notes.append((root, eighth_dur, vel))
        else:
            # Off-beats: strong syncopated hits
            beat = eighth // 2
            if beat in (0, 2):
                pitch = root
                vel = random.randint(80, 100)
            else:
                pitch = fifth if random.random() < 0.5 else third
                vel = random.randint(65, 85)
            notes.append((pitch, eighth_dur, vel))

    return notes


def _get_walking_note(root: int, last_root: int,
                      scale_notes_midi: List[int]) -> int:
    """
    Get a note for walking bass: a scale tone near the current root
    that creates smooth stepwise motion.
    """
    candidates = list(scale_notes_midi)

    # Filter to bass register
    candidates = [n for n in candidates if 24 <= n <= 48]

    if not candidates:
        # Create a chromatic approach
        if root > last_root:
            return root - 2  # Step down from above
        else:
            return root + 2  # Step up from below

    # Find a note that's close to the last root for stepwise motion
    best = random.choice(candidates)
    best_diff = abs(best - last_root)
    for n in candidates:
        diff = abs(n - last_root)
        # Prefer stepwise motion (2-5 semitones)
        if 2 <= diff <= 5 and diff < best_diff:
            best = n
            best_diff = diff

    # Ensure in bass register
    while best > 48:
        best -= 12
    while best < 24:
        best += 12

    return best


def generate_bassline_progression(config: GenerationConfig,
                                   output_path: str) -> List[Tuple[int, float, int]]:
    """Generate bassline progression and save to MIDI file."""
    notes = generate_bassline(config)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes