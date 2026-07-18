"""
Fit Checker - Analyzes generated MIDI tracks for compatibility and quality.
Produces pass/fail score report with human-readable issues.
Heuristic-based, not a music AI model.

Enhanced with:
- check_call_and_answer(): verify counter-melody only plays when melody rests
- check_register_separation(): ensure no two tracks crowd the same octave
- check_syncopation_density(): verify vocal chops have high syncopation
- check_all_tracks() updated to handle 7 tracks
"""

from typing import List, Tuple, Dict, Any, Optional
import mido


def build_scale_semitone_set(root_note: str, scale_mode: str) -> set:
    """
    Build a set of valid semitone intervals (0-11) for the given scale.
    
    For example, C major = {0, 2, 4, 5, 7, 9, 11} (C, D, E, F, G, A, B).
    Any note's pitch_class = pitch % 12 is checked against this set.
    
    Args:
        root_note: Note name like 'C', 'G', etc.
        scale_mode: Scale mode like 'major', 'natural_minor', etc.
    
    Returns:
        Set of valid semitone offsets from the root (0-11)
    """
    from generators.common import SCALE_TABLES, GM_NOTES
    
    if scale_mode not in SCALE_TABLES:
        return set(range(12))  # all notes valid as fallback
    
    root_midi = GM_NOTES.get(root_note, 60)
    root_semitone = root_midi % 12
    intervals = SCALE_TABLES[scale_mode]
    # Convert relative degrees to absolute semitones
    semitones = {(root_semitone + d) % 12 for d in intervals}
    return semitones


def check_key_conformity(midi_file_path: str, scale_semitones: set,
                         track_name: str = "",
                         allow_passing_tones: bool = True) -> Dict[str, Any]:
    """
    Check if notes in a MIDI file conform to the selected scale.
    
    Uses pitch-class (pitch % 12) matching so notes in ANY octave are checked correctly.

    Args:
        midi_file_path: Path to the MIDI file
        scale_semitones: Set of valid semitone values (0-11) from build_scale_semitone_set()
        track_name: Name of the track (for targeted leniency)
        allow_passing_tones: Whether to allow occasional out-of-scale notes

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True
    total_notes = 0
    out_of_scale_count = 0

    # Tracks that intentionally use chromatic approach notes — be more lenient
    chromatic_tracks = {'vocal chops', 'vocal_chops', 'turnaround fills', 
                        'turnaround_fills', 'counter-melody', 'counter_melody'}
    is_chromatic_track = track_name.lower().replace(' ', '_') in chromatic_tracks

    try:
        midi = mido.MidiFile(midi_file_path)

        for track in midi.tracks:
            for msg in track:
                if msg.type != 'note_on' or msg.velocity == 0:
                    continue

                pitch = msg.note
                total_notes += 1
                pitch_class = pitch % 12

                # Check if this pitch's semitone is in the scale
                if pitch_class not in scale_semitones:
                    out_of_scale_count += 1

                    if is_chromatic_track:
                        # Chromatic tracks: heavily lenient (they use approach notes on purpose)
                        if out_of_scale_count > total_notes * 0.5:
                            score -= 5
                            issues.append(f"Chromatic track {track_name}: high out-of-scale ratio at pitch {pitch}")
                    elif allow_passing_tones and out_of_scale_count / max(total_notes, 1) < 0.2:
                        # Allow up to 20% passing tones
                        pass  # Just count it, don't penalize
                    else:
                        score -= 15
                        issues.append(f"Out-of-scale note: pitch {pitch} (class {pitch_class}) not in scale")
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


def check_call_and_answer(melody_path: str, counter_melody_path: str) -> Dict[str, Any]:
    """
    Verify that counter-melody only plays when main melody rests or holds long notes.

    This checks mutual exclusion: they should not play simultaneously on strong beats.

    Args:
        melody_path: Path to the main melody MIDI file
        counter_melody_path: Path to the counter-melody MIDI file

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        # Collect melody note-on times
        melody_times = set()
        try:
            mmidi = mido.MidiFile(melody_path)
            for track in mmidi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        melody_times.add(msg.time)
        except Exception:
            pass

        # Collect counter-melody note-on times
        counter_times = set()
        try:
            cmidi = mido.MidiFile(counter_melody_path)
            for track in cmidi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        counter_times.add(msg.time)
        except Exception:
            pass

        # Check for overlap
        overlap_count = 0
        for ct in counter_times:
            # Check if any melody note is within 0.1s of this counter-melody note
            for mt in melody_times:
                if abs(ct - mt) < 0.1:
                    overlap_count += 1
                    break

        if overlap_count > len(counter_times) * 0.3:
            score -= 30
            issues.append(f"Counter-melody overlaps with melody on {overlap_count} notes "
                          f"(should only play during melody rests)")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking call-and-answer: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_register_separation(track_registers: Dict[str, Tuple[int, int]]) -> Dict[str, Any]:
    """
    Ensure no two tracks crowd the same octave range.

    Args:
        track_registers: Dict of track_name -> (min_pitch, max_pitch) for each track

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    track_names = list(track_registers.keys())
    for i in range(len(track_names)):
        for j in range(i + 1, len(track_names)):
            name_a = track_names[i]
            name_b = track_names[j]
            min_a, max_a = track_registers[name_a]
            min_b, max_b = track_registers[name_b]

            # Check if ranges overlap significantly (>50% overlap)
            overlap_min = max(min_a, min_b)
            overlap_max = min(max_a, max_b)
            if overlap_min < overlap_max:
                overlap_range = overlap_max - overlap_min
                range_a = max_a - min_a
                range_b = max_b - min_b

                if range_a > 0 and range_b > 0:
                    overlap_ratio_a = overlap_range / range_a
                    overlap_ratio_b = overlap_range / range_b

                    if overlap_ratio_a > 0.5 and overlap_ratio_b > 0.5:
                        score -= 15
                        issues.append(f"Register crowding: {name_a} ({min_a}-{max_a}) "
                                      f"and {name_b} ({min_b}-{max_b}) overlap significantly")
                    elif overlap_ratio_a > 0.3 or overlap_ratio_b > 0.3:
                        score -= 5
                        issues.append(f"Minor register overlap: {name_a} and {name_b}")

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_syncopation_density(midi_file_path: str) -> Dict[str, Any]:
    """
    Verify that vocal chops have high syncopation.
    Syncopation is measured by the ratio of notes played on off-beats vs on-beats.

    Args:
        midi_file_path: Path to the vocal chops MIDI file

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        midi = mido.MidiFile(midi_file_path)
        total_notes = 0
        off_beat_notes = 0

        for track in midi.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    total_notes += 1
                    # Consider a note syncopated if its time doesn't fall on
                    # a perfect 8th-note grid boundary
                    # (time modulo 0.5 beats should be > 0.1 for syncopation)
                    time_in_beats = msg.time * 0.1  # rough conversion
                    grid_offset = time_in_beats % 0.5
                    if grid_offset > 0.1 and grid_offset < 0.4:
                        off_beat_notes += 1

        if total_notes > 0:
            syncopation_ratio = off_beat_notes / total_notes
            if syncopation_ratio < 0.15:
                score -= 25
                issues.append(f"Low syncopation density: {syncopation_ratio:.1%} "
                              f"(expected > 15% for vocal chops)")
            elif syncopation_ratio < 0.25:
                score -= 5
                issues.append(f"Moderate syncopation: {syncopation_ratio:.1%}")
            else:
                issues.append(f"Good syncopation density: {syncopation_ratio:.1%}")
        else:
            issues.append("No notes found for syncopation check")
            score -= 10

    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking syncopation: {e}"]}

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
                        time_sec = tick_time / 480.0 * (60.0 / config.bpm)
                        if time_sec not in chord_notes_at_time:
                            chord_notes_at_time[time_sec] = []
                        chord_notes_at_time[time_sec].append(msg.note)
                        chord_change_times.append(time_sec)

            for time_sec, notes in chord_notes_at_time.items():
                chord_progression_notes.append((notes[0], 1.0))
        except Exception:
            pass

    # Build scale semitone set for correct octave-aware key checking
    scale_semitones = build_scale_semitone_set(config.root_note, config.scale_mode)

    # Check each track individually for key conformity
    for track_name, midi_path in midi_files.items():
        track_lower = track_name.lower()
        if track_lower in ('chords', 'hihats', 'hi-hats', 'kick', 'snare'):
            continue  # These don't need scale conformity

        result = check_key_conformity(midi_path, scale_semitones, track_name=track_name)
        if not result['passed']:
            total_score -= (100 - result['score']) * 0.2
            for issue in result['issues']:
                total_issues.append(f"{track_name}: {issue}")

    # Check harmonic clashes between melody and chords
    melody_path = midi_files.get('Melody') or midi_files.get('melody')
    if melody_path and chord_path:
        harmony_result = check_harmonic_clash(melody_path, chord_progression_notes, scale_notes_midi)
        total_score -= (100 - harmony_result['score']) * 0.15
        if not harmony_result['passed']:
            for issue in harmony_result['issues']:
                total_issues.append(f"Harmony: {issue}")

    # Check rhythmic alignment between bassline and chords
    bassline_path = midi_files.get('Bassline') or midi_files.get('bassline')
    if bassline_path and chord_change_times:
        rhythm_result = check_rhythmic_alignment(bassline_path, chord_change_times, config.bpm)
        total_score -= (100 - rhythm_result['score']) * 0.15
        if not rhythm_result['passed']:
            for issue in rhythm_result['issues']:
                total_issues.append(f"Rhythm: {issue}")

    # Check call-and-answer between melody and counter-melody
    counter_path = midi_files.get('Counter-Melody') or midi_files.get('counter_melody')
    if melody_path and counter_path:
        ca_result = check_call_and_answer(melody_path, counter_path)
        total_score -= (100 - ca_result['score']) * 0.1
        if not ca_result['passed']:
            for issue in ca_result['issues']:
                total_issues.append(f"Call&Answer: {issue}")

    # Check register separation between all tracks
    track_registers: Dict[str, Tuple[int, int]] = {}
    for track_name, midi_path in midi_files.items():
        try:
            midi = mido.MidiFile(midi_path)
            pitches = []
            for track in midi.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        pitches.append(msg.note)
            if pitches:
                track_registers[track_name] = (min(pitches), max(pitches))
        except Exception:
            pass

    if len(track_registers) >= 2:
        reg_result = check_register_separation(track_registers)
        total_score -= (100 - reg_result['score']) * 0.1
        if not reg_result['passed']:
            for issue in reg_result['issues']:
                total_issues.append(f"Register: {issue}")

    # Check syncopation density for vocal chops
    vocal_path = midi_files.get('Vocal Chops') or midi_files.get('vocal_chops')
    if vocal_path:
        sync_result = check_syncopation_density(vocal_path)
        total_score -= (100 - sync_result['score']) * 0.1
        if not sync_result['passed']:
            for issue in sync_result['issues']:
                total_issues.append(f"Syncopation: {issue}")

    overall_pass = total_score >= 60

    return {
        'passed': overall_pass,
        'overall_score': max(0, int(total_score)),
        'issues': total_issues if total_issues else ['All checks passed!']
    }


def get_register_range(generator_type: str) -> Tuple[int, int]:
    """Get recommended register range for a generator type."""
    ranges = {
        'bassline': (24, 48),
        'chords': (36, 60),
        'melody': (60, 84),
        'counter_melody': (72, 96),
        'vocal_chops': (72, 96),
        'turnaround_fills': (60, 84),
        'hihats': (42, 46),
    }
    return ranges.get(generator_type, (42, 84))