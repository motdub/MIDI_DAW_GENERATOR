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


def _extract_notes_with_abs_time(midi_file_path: str) -> List[Tuple[int, float, int]]:
    """
    Extract (pitch, abs_time_seconds, velocity) from a MIDI file.
    
    Properly accumulates delta ticks to produce absolute times in seconds.
    Uses the file's tempo track to convert ticks → seconds.
    """
    notes: List[Tuple[int, float, int]] = []
    try:
        midi = mido.MidiFile(midi_file_path)
        ticks_per_beat = midi.ticks_per_beat
        tempo = 500000  # default: 120 BPM = 500000 µs/beat
        
        for track in midi.tracks:
            abs_ticks = 0
            for msg in track:
                abs_ticks += msg.time
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                elif msg.type == 'note_on' and msg.velocity > 0:
                    # ticks → seconds: ticks / ticks_per_beat * (tempo / 1_000_000)
                    abs_seconds = (abs_ticks / ticks_per_beat) * (tempo / 1_000_000.0)
                    notes.append((msg.note, abs_seconds, msg.velocity))
    except Exception:
        pass
    return notes


def _extract_chord_timeline(midi_file_path: str, bpm: int = 120) -> List[Tuple[float, List[int]]]:
    """
    Extract a chord timeline from a MIDI file.
    
    Returns a list of (abs_time_seconds, [list_of_simultaneous_pitches]) sorted by time.
    Groups notes that start at the same time into chord blocks.
    """
    raw_notes = _extract_notes_with_abs_time(midi_file_path)
    if not raw_notes:
        return []
    
    # Sort by absolute time
    raw_notes.sort(key=lambda x: x[1])
    
    # Group simultaneous notes (within 5ms tolerance)
    TOLERANCE_SEC = 0.005
    groups: List[Tuple[float, List[int]]] = []
    current_time = raw_notes[0][1]
    current_pitches = [raw_notes[0][0]]
    
    for pitch, abs_time, vel in raw_notes[1:]:
        if abs(abs_time - current_time) <= TOLERANCE_SEC:
            current_pitches.append(pitch)
        else:
            groups.append((current_time, current_pitches))
            current_time = abs_time
            current_pitches = [pitch]
    
    if current_pitches:
        groups.append((current_time, current_pitches))
    
    return groups


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


def check_harmonic_clash(melody_path: str, chord_timeline: List[Tuple[float, List[int]]],
                         scale_notes: List[int]) -> Dict[str, Any]:
    """
    Check for harmonic clashes between melody and chords.
    
    Only compares each melody note against the chord that is actually
    sounding at that absolute time — not every chord in the progression.

    Args:
        melody_path: Path to the melody MIDI file
        chord_timeline: List of (abs_time_seconds, [simultaneous_pitches]) from _extract_chord_timeline
        scale_notes: List of MIDI note numbers for the scale (unused, kept for signature compat)

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        melody_notes = _extract_notes_with_abs_time(melody_path)
        if not melody_notes:
            return {'passed': True, 'score': 100, 'issues': ['No melody notes found']}
        if not chord_timeline:
            return {'passed': True, 'score': 100, 'issues': ['No chord timeline available']}

        # Build a list of (start_time, end_time, chord_pitches) for each chord block
        chord_blocks = []
        for i, (abs_time, pitches) in enumerate(chord_timeline):
            if i + 1 < len(chord_timeline):
                end_time = chord_timeline[i + 1][0]
            else:
                end_time = abs_time + 4.0  # assume 4 seconds if last chord
            chord_blocks.append((abs_time, end_time, pitches))

        # For each melody note, find the chord that's sounding at its time
        for pitch, abs_time, vel in melody_notes:
            # Find the chord block containing this time
            sounding_chord = None
            for start_t, end_t, pitches in chord_blocks:
                if start_t <= abs_time < end_t:
                    sounding_chord = pitches
                    break
            
            if sounding_chord is None:
                continue  # no chord at this time, skip

            for chord_pitch in sounding_chord:
                interval = abs(pitch - chord_pitch)
                # Only flag seconds (1 or 2 semitones) — thirds and beyond are consonant
                if interval == 1:
                    score -= 15
                    issues.append(f"Dissonant minor 2nd at {abs_time:.2f}s: "
                                  f"melody pitch {pitch} vs chord note {chord_pitch}")
                    break  # one clash per note is enough
                elif interval == 2:
                    score -= 8
                    issues.append(f"Dissonant major 2nd at {abs_time:.2f}s: "
                                  f"melody pitch {pitch} vs chord note {chord_pitch}")
                    break
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking harmony: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_rhythmic_alignment(bassline_path: str, chord_change_times: List[float],
                             bpm: int = 120) -> Dict[str, Any]:
    """
    Check if bassline note-onsets align with chord changes.
    
    Uses properly extracted absolute times (seconds) for bassline notes
    and compares against chord change times (also in seconds).

    Args:
        bassline_path: Path to the bassline MIDI file
        chord_change_times: List of absolute times (seconds) when chords change
        bpm: Beats per minute (for timing tolerance)

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        bassline_notes = _extract_notes_with_abs_time(bassline_path)
        if not bassline_notes:
            return {'passed': True, 'score': 100, 'issues': ['No bassline notes found']}

        # Extract just the absolute times
        bass_times = [t for _, t, _ in bassline_notes]
        quarter_beat = 60.0 / bpm / 4.0  # quarter-beat window in seconds

        for chord_time in chord_change_times:
            found_nearby = any(abs(bt - chord_time) < quarter_beat for bt in bass_times)
            if not found_nearby:
                score -= 25
                issues.append(f"Bass note onset missing near chord change at {chord_time:.2f}s")
    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking rhythm: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_call_and_answer(melody_path: str, counter_melody_path: str) -> Dict[str, Any]:
    """
    Verify that counter-melody only plays when main melody rests or holds long notes.
    
    Uses properly extracted absolute times (seconds) for both tracks.

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
        melody_notes = _extract_notes_with_abs_time(melody_path)
        counter_notes = _extract_notes_with_abs_time(counter_melody_path)

        if not melody_notes or not counter_notes:
            return {'passed': True, 'score': 100, 'issues': []}

        melody_times = set(t for _, t, _ in melody_notes)
        counter_times = set(t for _, t, _ in counter_notes)

        # Check for overlap (within 0.1s = 100ms window)
        overlap_count = 0
        for ct in counter_times:
            if any(abs(ct - mt) < 0.1 for mt in melody_times):
                overlap_count += 1

        overlap_ratio = overlap_count / max(len(counter_times), 1)
        if overlap_ratio > 0.3:
            score -= 30
            issues.append(f"Counter-melody overlaps with melody on {overlap_count}/{len(counter_times)} notes "
                          f"({overlap_ratio:.0%}, should be <30% for call-and-answer style)")
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
    
    Uses properly extracted absolute times to determine if notes fall
    on off-beats vs on-beats of a 16th-note grid.

    Args:
        midi_file_path: Path to the vocal chops MIDI file

    Returns:
        Dict with 'passed', 'score', and 'issues' keys
    """
    issues = []
    score = 100
    passed = True

    try:
        notes = _extract_notes_with_abs_time(midi_file_path)
        if not notes:
            return {'passed': True, 'score': 100, 'issues': ['No vocal chop notes found']}

        total_notes = len(notes)
        # 16th-note duration at 120 BPM is ~0.125s — we check for off-16th positions
        # A note is "syncopated" if its time mod 0.25 (16th) is between 0.05 and 0.20
        off_beat_notes = 0
        for _, abs_time, _ in notes:
            sixteenth_phase = (abs_time % 0.25)
            # On-beat = 0.00-0.05 or 0.20-0.25; off-beat = 0.05-0.20
            if 0.05 < sixteenth_phase < 0.20:
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

    except Exception as e:
        return {'passed': False, 'score': 0, 'issues': [f"Error checking syncopation: {e}"]}

    if score < 70:
        passed = False

    return {'passed': passed, 'score': max(0, score), 'issues': issues}


def check_all_tracks(config: Any, midi_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Run all fit checks on generated MIDI files.
    
    Uses proper absolute-time extraction for all timing-sensitive checks.

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

    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)

    # ---- Extract chord timeline with full chord voicings ----
    chord_path = midi_files.get('Chords') or midi_files.get('chords')
    chord_change_times: List[float] = []
    chord_timeline: List[Tuple[float, List[int]]] = []

    if chord_path:
        chord_timeline = _extract_chord_timeline(chord_path, config.bpm)
        chord_change_times = [t for t, _ in chord_timeline]

    # ---- Key conformity ----
    scale_semitones = build_scale_semitone_set(config.root_note, config.scale_mode)
    for track_name, midi_path in midi_files.items():
        track_lower = track_name.lower().replace(' ', '_')
        # Skip percussion and accompaniment tracks
        if track_lower in ('chords', 'hihats', 'hi-hats', 'kick', 'snare'):
            continue

        result = check_key_conformity(midi_path, scale_semitones, track_name=track_name)
        if not result['passed']:
            total_score -= (100 - result['score']) * 0.2
            for issue in result['issues']:
                total_issues.append(f"Key: {issue}")

    # ---- Harmony check (melody vs actual chord voicings) ----
    melody_path = midi_files.get('Melody') or midi_files.get('melody')
    if melody_path and chord_timeline:
        harmony_result = check_harmonic_clash(melody_path, chord_timeline, scale_notes_midi)
        total_score -= (100 - harmony_result['score']) * 0.15
        if not harmony_result['passed']:
            for issue in harmony_result['issues']:
                total_issues.append(f"Harmony: {issue}")

    # ---- Rhythmic alignment (bassline vs chord changes) ----
    bassline_path = midi_files.get('Bassline') or midi_files.get('bassline')
    if bassline_path and chord_change_times:
        rhythm_result = check_rhythmic_alignment(bassline_path, chord_change_times, config.bpm)
        total_score -= (100 - rhythm_result['score']) * 0.15
        if not rhythm_result['passed']:
            for issue in rhythm_result['issues']:
                total_issues.append(f"Rhythm: {issue}")

    # ---- Call-and-answer (melody vs counter-melody) ----
    counter_path = midi_files.get('Counter-Melody') or midi_files.get('counter_melody')
    if melody_path and counter_path:
        ca_result = check_call_and_answer(melody_path, counter_path)
        total_score -= (100 - ca_result['score']) * 0.1
        if not ca_result['passed']:
            for issue in ca_result['issues']:
                total_issues.append(f"Call&Answer: {issue}")

    # ---- Register separation ----
    # Exclude percussion tracks from register analysis
    perc_tracks = {'hihats', 'hi-hats', 'kick', 'snare'}
    track_registers: Dict[str, Tuple[int, int]] = {}
    for track_name, midi_path in midi_files.items():
        if track_name.lower().replace(' ', '_') in perc_tracks:
            continue
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

    # ---- Syncopation density (vocal chops) ----
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