"""
Shared utilities for MIDI generation - scale, key, tempo helpers.
Pure Python, no external dependencies beyond mido.
"""

from dataclasses import dataclass
from typing import List, Tuple, Callable, Any
import random


# GM Standard MIDI Note Numbers (A0 = 21)
GM_NOTES = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63, 'E': 64,
    'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68, 'Ab': 68, 'A': 69,
    'A#': 70, 'Bb': 70, 'B': 71,
}

# Scale tables - note names for each scale degree in a given root key
SCALE_TABLES = {
    'major': [0, 2, 4, 5, 7, 9, 11],      # C major: C D E F G A B
    'natural_minor': [0, 2, 3, 5, 7, 8, 10],  # A minor: A B C D E F G
    'dorian': [0, 2, 3, 5, 6, 8, 10],       # D dorian: D E F G A B C
    'phrygian': [0, 1, 3, 5, 7, 8, 10],     # E phrygian: E F G A B C D
    'lydian': [0, 2, 4, 6, 7, 9, 11],       # F lydian: F G A B C D E
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],   # G mixolydian: G A B C D E F
    'aeolian': [0, 2, 3, 5, 6, 8, 10],      # A aeolian (same as natural minor)
    'ionian': [0, 2, 4, 5, 7, 9, 11],       # C ionian (same as major)
}

# Chord templates - scale degrees for each chord type
CHORD_TEMPLATES = {
    'i': [0, 3, 7],      # minor triad: root, third, fifth
    'ii': [2, 4, 7],     # diminished triad (in natural minor)
    'iii': [4, 6, 10],   # major triad
    'IV': [5, 7, 10],    # minor triad
    'V': [7, 9, 11],     # dominant 7th (in natural minor) or major
    'vi': [9, 11, 14],   # minor triad
    'VII': [10, 12, 15],  # augmented triad (in natural minor)
}

# Common chord progressions - list of scale degree chords
CHORD_PROGRESSIONS = {
    'I-V-vi-IV': ['I', 'V', 'vi', 'IV'],
    'ii-V-I': ['II', 'V', 'I'],
    'iv-vi-iii-II': ['IV', 'VI', 'III', 'VII'],
    'I-IV-V-vi': ['I', 'IV', 'V', 'vi'],
}


@dataclass
class GenerationConfig:
    """Shared configuration for all generators."""
    root_note: str  # e.g., "C", "A"
    scale_mode: str  # e.g., "major", "natural_minor"
    bpm: int = 120   # beats per minute
    bar_length: int = 8  # number of bars to generate
    seed: int | None = None


def get_scale_notes(root_note: str, scale_mode: str) -> List[str]:
    """Get list of note names for the given root and scale mode."""
    if scale_mode not in SCALE_TABLES:
        raise ValueError(f"Unknown scale mode: {scale_mode}")

    # Get the base notes from the scale table (relative to root)
    relative_notes = SCALE_TABLES[scale_mode]

    # Convert relative degrees to absolute note numbers
    absolute_notes = []
    for degree in relative_notes:
        if 0 <= degree < len(GM_NOTES):
            abs_note = GM_NOTES[root_note] + degree
            abs_note_name = get_note_name(abs_note)
            absolute_notes.append(abs_note_name)

    return absolute_notes


def get_scale_notes_midi(root_note: str, scale_mode: str) -> List[int]:
    """Get list of MIDI note numbers for the given root and scale mode."""
    note_names = get_scale_notes(root_note, scale_mode)
    return [get_midi_note_from_name(n) for n in note_names]


def get_chord_from_scale_degree(scale_mode: str, chord_type: str,
                                 root_note: str) -> Tuple[str, List[int]]:
    """Get a chord name and its note numbers for the given scale degree."""
    if scale_mode not in SCALE_TABLES:
        raise ValueError(f"Unknown scale mode: {scale_mode}")

    relative_notes = SCALE_TABLES[scale_mode]
    # Roman numeral to integer mapping (handles both uppercase and lowercase)
    roman_to_int = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7,
        'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
        'vi': 6, 'vii': 7,
    }
    # Find the scale degree for this chord type (use original case)
    try:
        scale_degree = roman_to_int[chord_type]
    except KeyError:
        # Fallback: treat as string index in relative_notes
        scale_degree = relative_notes.index(chord_type) if chord_type in relative_notes else 0

    # Normalize chord type to lowercase for lookup
    chord_type_lower = chord_type.lower()

    # Get the chord's note numbers from its template
    chord_notes = []
    for degree in CHORD_TEMPLATES[chord_type_lower]:
        if 0 <= degree < len(GM_NOTES):
            abs_note = GM_NOTES[root_note] + (degree % len(relative_notes))
            chord_notes.append(abs_note)

    return get_chord_name(root_note, chord_type), chord_notes


def get_note_name(note_number: int) -> str:
    """Convert MIDI note number to note name."""
    octave = note_number // 12 - 1
    note_in_octave = note_number % 12

    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return f"{notes[note_in_octave]}{octave}"


def get_chord_name(root_note: str, chord_type: str) -> str:
    """Get a Roman numeral chord name."""
    # Map to uppercase for standard notation
    type_map = {
        'i': 'i', 'ii': 'ii', 'iii': 'III',
        'IV': 'iv', 'V': 'V', 'VI': 'vi', 'VII': 'VII'
    }

    # Determine quality based on root note and chord type (use original case)
    if chord_type in ['I', 'III', 'VI']:
        return f"{type_map[chord_type]}{root_note}"
    elif chord_type in ['ii', 'iv', 'vii']:
        return f"{type_map[chord_type].lower()}{root_note}"
    else:
        return f"{type_map[chord_type]}{root_note}"


def get_midi_note_from_name(note_name: str) -> int:
    """Convert note name (e.g., 'C4') to MIDI note number."""
    if not note_name:
        return 60  # Default to C4

    # Separate the note letter from the octave number
    note = note_name.rstrip('0123456789')
    octave_str = note_name[len(note):]

    if not note:
        return 60

    octave = int(octave_str) if octave_str else 4

    # Handle sharps/flats in the note name
    if note in GM_NOTES:
        base_val = GM_NOTES[note]
    else:
        # Try to find it (e.g., 'C#4' -> 'C#' at octave 4)
        try:
            base_val = GM_NOTES[note]
        except KeyError:
            raise ValueError(f"Invalid note name: {note_name}")

    return (octave + 1) * 12 + (base_val - 60)


def get_chord_notes_from_name(chord_name: str) -> List[int]:
    """Get MIDI note numbers for a chord name like 'Cmaj7' or 'Am7'."""
    # Parse the chord name
    parts = chord_name.split()
    root_note = parts[0]

    # Determine quality from remaining parts
    quality = ''
    if len(parts) > 1:
        quality = parts[1].lower()
        if quality == 'maj' or quality == 'major':
            quality = 'Maj7'
        elif quality == 'min' or quality == 'minor':
            quality = 'm7'
        elif quality == 'dim' or quality == 'half-dim':
            quality = 'dim7'
        elif quality == 'aug' or quality == 'augmented':
            quality = 'aug7'

    # Get the root note's MIDI number
    try:
        root_midi = get_midi_note_from_name(root_note)
    except ValueError as e:
        raise ValueError(f"Invalid chord name: {chord_name}. Error: {e}")

    # Calculate based on quality
    if 'Maj7' in quality or 'major' in quality:
        return [root_midi, root_midi + 4, root_midi + 7, root_midi + 10]
    elif 'm7' in quality or 'minor' in quality:
        return [root_midi, root_midi + 3, root_midi + 7, root_midi + 10]
    elif 'dim7' in quality:
        return [root_midi, root_midi + 3, root_midi + 6, root_midi + 9]
    else:
        # Default to major triad
        return [root_midi, root_midi + 4, root_midi + 7]


def get_scale_from_root_and_mode(root_note: str, scale_mode: str) -> List[int]:
    """Get MIDI note numbers for a scale."""
    return get_scale_notes_midi(root_note, scale_mode)


def get_chord_progression_for_key(root_note: str, scale_mode: str,
                                   progression_type: str | None = None) -> List[str]:
    """Get a list of chord names for the given key and optional progression type."""
    # If no specific progression requested, use I-V-vi-IV as default
    if not progression_type or progression_type == 'default':
        prog_type = 'I-V-vi-IV'
    else:
        prog_type = progression_type

    # Get scale notes to determine which chord types are available
    scale_notes = get_scale_notes(root_note, scale_mode)

    # Map Roman numerals to actual note names based on the scale
    chords = []
    for roman in CHORD_PROGRESSIONS[prog_type]:
        if roman == 'I':
            # Find major triad starting from root
            chord_name = get_chord_from_scale_degree(scale_mode, 'III', root_note)[0]
        elif roman == 'V':
            # Find dominant 7th (or major) - typically V in major, bVII in minor
            if scale_mode.startswith('minor'):
                chord_name = get_chord_from_scale_degree(scale_mode, 'VII', root_note)[0]
            else:
                chord_name = get_chord_from_scale_degree(scale_mode, 'V', root_note)[0]
        elif roman == 'vi':
            # Find minor triad starting from 6th degree
            chord_name = get_chord_from_scale_degree(scale_mode, 'VI', root_note)[0]
        elif roman == 'IV':
            # Find minor triad starting from 4th degree
            chord_name = get_chord_from_scale_degree(scale_mode, 'iv', root_note)[0]
        else:
            # For ii, iii, etc., use the appropriate quality
            chord_name = get_chord_from_scale_degree(scale_mode, roman, root_note)[0]

        chords.append(chord_name)

    return chords


def generate_midi_file(config: GenerationConfig,
                       note_data: List[Tuple[int, float]],
                       output_path: str,
                       velocity: int = 80):
    """
    Generate a MIDI file from note data.

    Args:
        config: Generation configuration (bpm, etc.)
        note_data: List of (pitch, duration_seconds) tuples
        output_path: Path to save the .mid file
        velocity: MIDI velocity (0-127) for all notes
    """
    from mido import MidiFile, MidiTrack, MetaMessage, Message

    # Create new MIDI file (Type 1 - single track)
    midi = MidiFile(type=1)
    track = MidiTrack()
    midi.tracks.append(track)

    # Set tempo meta event: tempo is microseconds per beat
    # 120 BPM = 500,000 microseconds per beat
    tempo_us_per_beat = int(60_000_000 / config.bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo_us_per_beat))

    # Default ticks per beat in mido is 480
    ticks_per_beat = 480
    seconds_per_tick = 60.0 / (config.bpm * ticks_per_beat)

    # Add notes
    current_tick = 0
    for pitch, duration_sec in note_data:
        duration_ticks = int(duration_sec / seconds_per_tick) if seconds_per_tick > 0 else 1

        # Note on
        track.append(Message('note_on', note=pitch, velocity=velocity, time=0))
        # Note off after duration (no delta time between note_on and note_off within same chord)
        track.append(Message('note_off', note=pitch, velocity=0, time=duration_ticks))

        # Advance tick position (for next note in sequence)
        current_tick += duration_ticks

    # End of track marker
    track.append(MetaMessage('end_of_track', time=0))

    # Save the MIDI file
    midi.save(output_path)


# Instead of using a generator_func pattern, each generator should just
# return List[Tuple[int, float]] and call generate_midi_file directly.
# This wrapper is kept for backward compatibility.
def generate_midi_file_from_func(config: GenerationConfig,
                                  generator_func: Callable[[GenerationConfig], List[Tuple[int, float]]],
                                  output_path: str):
    """Generate a MIDI file by calling a generator function."""
    note_data = generator_func(config)
    generate_midi_file(config, note_data, output_path)


def get_register_range(generator_type: str) -> Tuple[int, int]:
    """Get recommended register range for a generator type."""
    if generator_type == 'bassline':
        return (24, 36)  # Octave 2-3
    elif generator_type == 'chords':
        return (36, 50)  # Octave 3-4
    elif generator_type == 'melody':
        return (60, 84)  # Octave 5-6
    else:  # hihats - pitch doesn't matter much
        return (42, 42)  # GM closed hi-hat


def get_velocity_range(generator_type: str) -> Tuple[int, int]:
    """Get recommended velocity range for a generator type."""
    if generator_type == 'bassline':
        return (60, 95)
    elif generator_type == 'chords':
        return (40, 85)
    elif generator_type == 'melody':
        return (50, 100)
    else:  # hihats - velocity is more important than pitch
        return (70, 95)