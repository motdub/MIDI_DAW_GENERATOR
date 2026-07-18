"""
Counter-Melody Generator — Call-and-answer response to the main melody.

Logic:
  - Analyze the main melody track's note pattern
  - Whenever main melody has a rest OR a note longer than a half-note,
    the counter-melody triggers a fast 3-5 note phrase in a higher octave
  - Uses call-and-answer structure: melody = "call" (beats 1-2),
    counter-melody = "answer" (beats 3-4)
  - All notes are diatonic to the selected scale
  - Rhythm: mostly 16th notes, some triplet feel
  - Velocity: 60-100, ghost notes at 30-40

Output file: counter_melody.mid
"""

from typing import List, Tuple, Optional
import random

from generators.common import (
    GenerationConfig, get_scale_notes_midi, get_register_range,
    get_velocity_range, generate_midi_file, generate_midi_file_old,
    COUNTER_MELODY_PATTERNS, get_chord_at_position, build_chord_progression
)


def generate_counter_melody(config: GenerationConfig,
                            main_melody_pattern: Optional[List[Tuple[int, float, int]]] = None
                            ) -> List[Tuple[int, float, int]]:
    """
    Generate a counter-melody that responds to the main melody.

    The counter-melody uses call-and-answer phrasing:
    - When the main melody rests or holds a long note (> half-note / 2 beats),
      the counter-melody plays a fast 3-5 note phrase.
    - It plays in a higher octave (+12 to +19 semitones above the melody).
    - Rhythm is mostly 16th notes with occasional triplet feel.

    Args:
        config: Generation configuration
        main_melody_pattern: Optional list of (pitch, duration_sec, velocity)
                             from the main melody generator, used for rest/long-note detection.
                             If None, the counter-melody will generate its own independent pattern.

    Returns:
        List of (pitch, duration_seconds, velocity) tuples
    """
    # Seed RNG if provided
    if config.seed is not None:
        random.seed(config.seed)

    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)
    seconds_per_beat = 60.0 / config.bpm
    sixteenth_note = seconds_per_beat * 0.25  # 1/16 note
    half_note = seconds_per_beat * 2.0       # 2 beats = half note

    # Build chord progression for harmonic context
    chord_progression = build_chord_progression(config)

    # If we have main melody data, analyze it to find opportunities
    melody_rest_times: List[Tuple[float, float]] = []  # (start_sec, end_sec) of rests/long-notes
    if main_melody_pattern:
        melody_rest_times = _analyze_melody_for_opportunities(
            main_melody_pattern, sixteenth_note, half_note
        )

    all_notes: List[Tuple[int, float, int]] = []

    for bar in range(config.bar_length):
        # Determine which bar of the 8-bar phrase we're in (A=0-3, B=4-7)
        bar_in_phrase = bar % 8

        # Call bars (1-2 of each 4-bar half) → counter-melody is quiet
        # Answer bars (3-4 of each 4-bar half) → counter-melody responds
        is_call_bar = (bar_in_phrase % 4) < 2  # beats 1-2 = call
        is_answer_bar = not is_call_bar         # beats 3-4 = answer

        # Get chord notes for this bar
        _, chord_notes = get_chord_at_position(bar, 0, chord_progression)

        if is_answer_bar:
            # Generate answering phrase for beats 3-4
            phrase = _generate_answer_phrase(
                bar, chord_notes, scale_notes_midi,
                seconds_per_beat, sixteenth_note,
                config.root_note, config.scale_mode
            )
            all_notes.extend(phrase)
        elif is_call_bar:
            # Possibly add ghost notes or short fills on beat 2.5 or 4
            if random.random() < 0.3:
                ghost_note = _get_diatonic_note(chord_notes, scale_notes_midi, bar)
                # Ghost notes at low velocity
                all_notes.append((ghost_note + 12, sixteenth_note * 0.5, 30))

    # If we have melody rest times, also fill those gaps with counter-melody
    if melody_rest_times:
        fill_notes = _fill_melody_gaps(
            melody_rest_times, chord_progression, scale_notes_midi,
            seconds_per_beat, sixteenth_note, config.bar_length
        )
        all_notes.extend(fill_notes)

    return all_notes


def _analyze_melody_for_opportunities(
    melody_pattern: List[Tuple[int, float, int]],
    sixteenth_note: float,
    half_note: float
) -> List[Tuple[float, float]]:
    """
    Analyze the main melody pattern to find rests and long notes.

    Returns a list of (start_time, end_time) windows where the counter-melody
    can play without conflicting with the main melody.
    """
    rest_times: List[Tuple[float, float]] = []
    current_time = 0.0

    for pitch, duration, velocity in melody_pattern:
        if velocity == 0 or duration >= half_note:
            # This is either a rest (vel=0) or a long note
            # The counter-melody can play here
            rest_times.append((current_time, current_time + duration))
        current_time += duration

    return rest_times


def _fill_melody_gaps(
    melody_rest_times: List[Tuple[float, float]],
    chord_progression: List[Tuple[int, List[int]]],
    scale_notes_midi: List[int],
    seconds_per_beat: float,
    sixteenth_note: float,
    bar_length: int
) -> List[Tuple[int, float, int]]:
    """
    Fill gaps in the melody with counter-melody phrases.
    Each gap gets a 3-5 note phrase.
    """
    fill_notes: List[Tuple[int, float, int]] = []

    for gap_start, gap_end in melody_rest_times:
        gap_duration = gap_end - gap_start
        if gap_duration < sixteenth_note * 3:
            continue  # Gap too small to fill

        # Determine which bar/beat this gap occurs in
        bar_idx = int(gap_start / (seconds_per_beat * 4))
        _, chord_notes = get_chord_at_position(bar_idx, 0, chord_progression)

        # Generate 3-5 notes for this fill
        num_notes = random.randint(3, 5)
        note_duration = gap_duration / num_notes

        # Choose a pattern
        pattern_name = random.choice(list(COUNTER_MELODY_PATTERNS.keys()))
        pattern = COUNTER_MELODY_PATTERNS[pattern_name]

        for i in range(num_notes):
            if chord_notes:
                base_pitch = random.choice(chord_notes)
            else:
                base_pitch = 72  # C5 default

            # Apply pattern offset (wrap around pattern)
            offset = pattern[i % len(pattern)]
            pitch = base_pitch + offset + 12  # One octave above melody

            # Ensure pitch is in scale
            pitch = _snap_to_scale(pitch, scale_notes_midi)

            # Ensure register is 72-96
            while pitch < 72:
                pitch += 12
            while pitch > 96:
                pitch -= 12

            velocity = random.randint(60, 100)
            if i == 0 or i == num_notes - 1:
                velocity = random.randint(50, 70)  # Softer start/end

            fill_notes.append((pitch, note_duration, velocity))

    return fill_notes


def _generate_answer_phrase(
    bar: int,
    chord_notes: List[int],
    scale_notes_midi: List[int],
    seconds_per_beat: float,
    sixteenth_note: float,
    root_note: str,
    scale_mode: str
) -> List[Tuple[int, float, int]]:
    """
    Generate a call-and-answer phrase for beats 3-4 of a bar.

    The answer should be a fast 4-6 note phrase that responds to the
    implied "call" on beats 1-2.
    """
    notes: List[Tuple[int, float, int]] = []

    # Determine number of notes in the answer
    num_notes = random.choice([4, 5, 6])

    # Choose a pattern for the melodic shape
    pattern_name = random.choice(list(COUNTER_MELODY_PATTERNS.keys()))
    pattern = COUNTER_MELODY_PATTERNS[pattern_name]

    # Duration per note — fill 2 beats
    phrase_duration = seconds_per_beat * 2.0
    note_duration = phrase_duration / num_notes

    for i in range(num_notes):
        if chord_notes:
            base_pitch = random.choice(chord_notes)
        else:
            base_pitch = 72

        # Apply pattern offset
        offset = pattern[i % len(pattern)]
        pitch = base_pitch + offset + 12  # +1 octave above chord range

        # Snap to scale
        pitch = _snap_to_scale(pitch, scale_notes_midi)

        # Keep in register 72-96
        while pitch < 72:
            pitch += 12
        while pitch > 96:
            pitch -= 12

        # Velocity with accent on first and third notes
        if i == 0 or i == 3:
            velocity = random.randint(75, 100)
        elif i == num_notes - 1:
            velocity = random.randint(60, 80)  # Softer ending
        else:
            velocity = random.randint(50, 80)

        notes.append((pitch, note_duration, velocity))

    return notes


def _get_diatonic_note(chord_notes: List[int],
                       scale_notes_midi: List[int],
                       bar: int) -> int:
    """Get a diatonic note, preferring chord tones."""
    if chord_notes and random.random() < 0.6:
        return random.choice(chord_notes)
    elif scale_notes_midi:
        return random.choice(scale_notes_midi)
    return 72


def _snap_to_scale(pitch: int, scale_notes_midi: List[int]) -> int:
    """
    Snap a pitch to the nearest note in the scale.

    If the pitch is not in the scale, find the closest scale note
    in the same octave region. Also enforces counter-melody register (72-96).
    """
    if not scale_notes_midi:
        pitch = max(72, min(96, pitch))
        return pitch

    if pitch in scale_notes_midi:
        pitch = max(72, min(96, pitch))
        return pitch

    # Find the closest scale note within ±6 semitones
    best = pitch
    best_diff = 12
    for scale_note in scale_notes_midi:
        # Consider notes in the same octave region
        for octave_offset in range(-2, 3):
            candidate = scale_note + (octave_offset * 12)
            diff = abs(pitch - candidate)
            if diff < best_diff:
                best_diff = diff
                best = candidate

    # Clamp to register 72-96
    while best < 72:
        best += 12
    while best > 96:
        best -= 12

    return best


def generate_counter_melody_progression(config: GenerationConfig,
                                         output_path: str,
                                         main_melody_pattern: Optional[List[Tuple[int, float, int]]] = None
                                         ) -> List[Tuple[int, float, int]]:
    """Generate counter-melody and save to MIDI file."""
    notes = generate_counter_melody(config, main_melody_pattern)

    # Generate the MIDI file
    generate_midi_file(config, notes, output_path)

    return notes