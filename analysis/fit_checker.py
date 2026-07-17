"""
Fit Checker - Analyzes generated MIDI tracks for compatibility and quality.
Produces pass/fail score report with human-readable issues.
Heuristic-based, not a music AI model.
"""

from typing import List, Tuple, Dict, Any
import mido


def check_key_conformity(midi_file_path: str, scale_notes: List[int],
                         allow_passing_tones: bool = True) -> Dict[str, Any]:
    """
    Check if notes in a MIDI file conform to the selected scale.

    Args:
        midi_file_path: Path to the MIDI file
        scale_notes: List of MIDI note numbers for the scale
        allow_passing_tones: Whether to allow occasional out-of-scale notes

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True  # Default to passing
    total_notes = 0
    out_of_scale_count = 0

    try:
        midi = mido.MidiFile(midi_file_path)

        for track in midi.tracks:
            for msg in track:
                if msg.type != 'note_on' or msg.velocity == 0:
                    continue

                pitch = msg.note
                total_notes += 1

                # Check if note is in scale
                if pitch not in scale_notes:
                    out_of_scale_count += 1

                    # Allow some passing tones (up to 20% of notes)
                    if allow_passing_tones and out_of_scale_count / max(total_notes, 1) < 0.2:
                        issues.append(f"Out-of-scale note at time {msg.time}: pitch {pitch}")
                    else:
                        score -= 15
                        issues.append(f"Major out-of-scale cluster: time {msg.time}, pitch {pitch}")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error reading MIDI file: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_harmonic_clash(midi_file_path: str, chord_progression: List[Tuple[int, float]],
                         scale_notes: List[int]) -> Dict[str, Any]:
    """
    Check for harmonic clashes between melody and chords.

    Args:
        midi_file_path: Path to the MIDI file (melody)
        chord_progression: List of (pitch, duration) tuples for chord voicings
        scale_notes: List of MIDI note numbers for the scale

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        midi = mido.MidiFile(midi_file_path)

        # Collect all melody note-on events with their times
        melody_notes = []
        for track in midi.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    melody_notes.append((msg.note, msg.time))

        # For each melody note, check against the chord that would be playing
        # (simplified: check against first chord pitch for all)
        if not melody_notes:
            return {'passed': True, 'score': 100, 'issues': ['No melody notes found']}

        for pitch, time in melody_notes:
            for chord_pitch, chord_duration in chord_progression:
                interval = abs(pitch - chord_pitch)

                # Minor second (1 semitone) is highly dissonant
                if interval == 1:
                    score -= 20
                    issues.append(f"Dissonant minor 2nd at time {time}: "
                                  f"melody pitch {pitch} vs chord note {chord_pitch}")
                # Major second (2 semitones) is moderately dissonant
                elif interval == 2:
                    score -= 10
                    issues.append(f"Dissonant major 2nd at time {time}: "
                                  f"melody pitch {pitch} vs chord note {chord_pitch}")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking harmony: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_rhythmic_alignment(midi_file_path: str, chord_change_times: List[float],
                             bpm: int = 120) -> Dict[str, Any]:
    """
    Check if bassline note-onsets align with chord changes.

    Args:
        midi_file_path: Path to the MIDI file (bassline)
        chord_change_times: List of times (in seconds) when chords change
        bpm: Beats per minute (for timing reference)

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        midi = mido.MidiFile(midi_file_path)

        # Collect all note-on events
        bassline_notes = []
        for track in midi.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    bassline_notes.append((msg.note, msg.time))

        # For each chord change point, check if there's a bass note onset nearby
        for chord_time in chord_change_times:
            found_nearby = False
            for pitch, note_time in bassline_notes:
                # Check if note is within 1/4 beat of chord change
                quarter_beat = 60.0 / bpm / 4
                if abs(note_time - chord_time) < quarter_beat:
                    found_nearby = True
                    break

            if not found_nearby:
                score -= 25
                issues.append(f"Bass note onset missing near chord change at {chord_time:.2f}s")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking rhythm: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_register_overlap(midi_file_path: str, register_range: Tuple[int, int],
                           other_notes: List[Tuple[int, float]]) -> Dict[str, Any]:
    """
    Check if notes don't crowd the same octave range.

    Args:
        midi_file_path: Path to the MIDI file
        register_range: (min_pitch, max_pitch) for this track's register
        other_notes: List of (pitch, duration) from another track that might overlap

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        midi = mido.MidiFile(midi_file_path)

        for track in midi.tracks:
            for msg in track:
                if msg.type != 'note_on' or msg.velocity == 0:
                    continue

                pitch = msg.note

                # Check for overlap with other notes in similar register range
                for other_pitch, _ in other_notes:
                    if abs(pitch - other_pitch) < 12 and pitch != other_pitch:
                        score -= 5
                        issues.append(f"Register crowding at time {msg.time}: "
                                      f"pitch {pitch} overlaps with {other_pitch}")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking register: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_all_tracks(config: Any, midi_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Run all fit checks on generated MIDI files.

    Args:
        config: Generation configuration (bpm, root_note, scale_mode)
        midi_files: Dict mapping track name to file path (e.g. 'Bassline' -> 'bassline.mid')

    Returns:
        Dict with 'passed', 'overall_score', and 'issues' keys
    """
    total_issues: List[str] = []
    total_score = 100

    # Import here to avoid circular imports
    from generators.common import get_scale_notes_midi

    # Get scale notes for key conformity check
    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)

    # Build the chord progression from the midi_files dict
    # Find the chords file and extract notes
    chord_path = midi_files.get('Chords') or midi_files.get('chords')
    chord_change_times: List[float] = []
    chord_progression_notes: List[Tuple[int, float]] = []

    if chord_path:
        try:
            cmidi = mido.MidiFile(chord_path)
            chord_notes_at_time: Dict[float, List[int]] = {}
            for track in cmidi.tracks:
                tick_time = 0
                for msg in track:
                    if hasattr(msg, 'time'):
                        tick_time += msg.time
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Convert ticks to seconds (roughly)
                        time_sec = tick_time / 480.0 * (60.0 / config.bpm)
                        if time_sec not in chord_notes_at_time:
                            chord_notes_at_time[time_sec] = []
                        chord_notes_at_time[time_sec].append(msg.note)
                        chord_change_times.append(time_sec)

            # For each chord change, store a representative pitch (first note)
            for time_sec, notes in chord_notes_at_time.items():
                chord_progression_notes.append((notes[0], 1.0))
        except Exception:
            pass

    # Check each track individually
    for track_name, midi_path in midi_files.items():
        track_lower = track_name.lower()
        if track_lower == 'chords':
            # Chords don't need scale conformity check
            continue

        result = check_key_conformity(midi_path, scale_notes_midi)
        total_score -= (100 - result['score']) / 4

        if not result['passed']:
            for issue in result['issues']:
                total_issues.append(f"{track_name}: {issue}")

    # Check harmonic clashes between melody and chords
    melody_path = midi_files.get('Melody') or midi_files.get('melody')
    if melody_path and chord_path:
        harmony_result = check_harmonic_clash(melody_path, chord_progression_notes, scale_notes_midi)
        total_score -= (100 - harmony_result['score']) / 4

        if not harmony_result['passed']:
            for issue in harmony_result['issues']:
                total_issues.append(f"Harmony: {issue}")

    # Check rhythmic alignment between bassline and chords
    bassline_path = midi_files.get('Bassline') or midi_files.get('bassline')
    if bassline_path and chord_change_times:
        rhythm_result = check_rhythmic_alignment(bassline_path, chord_change_times, config.bpm)
        total_score -= (100 - rhythm_result['score']) / 4

        if not rhythm_result['passed']:
            for issue in rhythm_result['issues']:
                total_issues.append(f"Rhythm: {issue}")

    # Check register overlap between bassline and chords
    if bassline_path and chord_path:
        # Read chord notes for overlap check
        chord_notes_for_overlap: List[Tuple[int, float]] = []
        try:
            cmidi = mido.MidiFile(chord_path)
            for track in cmidi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        chord_notes_for_overlap.append((msg.note, msg.time))
        except Exception:
            pass

        bassline_result = check_register_overlap(bassline_path,
                                                  (24, 36),
                                                  chord_notes_for_overlap)
        total_score -= (100 - bassline_result['score']) / 4

        if not bassline_result['passed']:
            for issue in bassline_result['issues']:
                total_issues.append(f"Register: {issue}")

    overall_pass = total_score >= 70

    return {
        'passed': overall_pass,
        'overall_score': max(0, int(total_score)),
        'issues': total_issues if total_issues else ['All checks passed!']
    }


def get_register_range(generator_type: str) -> Tuple[int, int]:
    """Get recommended register range for a generator type."""
    if generator_type == 'bassline':
        return (24, 36)
    elif generator_type == 'chords':
        return (36, 50)
    elif generator_type == 'melody':
        return (60, 84)
    else:
        return (42, 46)