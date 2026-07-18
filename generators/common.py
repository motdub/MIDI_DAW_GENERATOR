"""
Shared utilities for MIDI generation - scale, key, tempo helpers.
Pure Python, no external dependencies beyond mido.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Any, Optional
import random


# GM Standard MIDI Note Numbers (A0 = 21)
GM_NOTES = {
    'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63, 'E': 64,
    'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68, 'Ab': 68, 'A': 69,
    'A#': 70, 'Bb': 70, 'B': 71,
}

# Scale tables - note names for each scale degree in a given root key
SCALE_TABLES = {
    'major': [0, 2, 4, 5, 7, 9, 11],          # C major: C D E F G A B
    'natural_minor': [0, 2, 3, 5, 7, 8, 10],   # A minor: A B C D E F G
    'dorian': [0, 2, 3, 5, 6, 8, 10],           # D dorian: D E F G A B C
    'phrygian': [0, 1, 3, 5, 7, 8, 10],         # E phrygian: E F G A B C D
    'lydian': [0, 2, 4, 6, 7, 9, 11],           # F lydian: F G A B C D E
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],       # G mixolydian: G A B C D E F
    'aeolian': [0, 2, 3, 5, 6, 8, 10],          # A aeolian (same as natural minor)
    'ionian': [0, 2, 4, 5, 7, 9, 11],           # C ionian (same as major)
}

# Chord templates - scale degrees for each chord type
CHORD_TEMPLATES = {
    'i': [0, 3, 7],       # minor triad: root, minor third, perfect fifth
    'ii': [2, 4, 7],      # diminished triad (in natural minor)
    'iii': [4, 6, 10],    # major triad on third degree
    'IV': [5, 7, 10],     # minor triad on fourth degree
    'V': [7, 9, 11],      # dominant 7th (in natural minor) or major
    'vi': [9, 11, 14],    # minor triad on sixth degree
    'VII': [10, 12, 15],  # augmented triad (in natural minor)
}

# Common chord progressions - list of scale degree chords
CHORD_PROGRESSIONS = {
    'I-V-vi-IV': ['I', 'V', 'vi', 'IV'],
    'ii-V-I': ['II', 'V', 'I'],
    'iv-vi-iii-II': ['IV', 'VI', 'III', 'VII'],
    'I-IV-V-vi': ['I', 'IV', 'V', 'vi'],
    'i-VI-III-VII': ['i', 'VI', 'III', 'VII'],  # common in minor
    'I-vi-IV-V': ['I', 'vi', 'IV', 'V'],          # 50s progression
}

# Counter-melody progression templates (call-and-answer intervals)
# These define the melodic shape: [root_offset, third_offset, fifth_offset]
COUNTER_MELODY_PATTERNS = {
    'minor_arpeggio_up': [0, 3, 7, 12, 15],      # C-Eb-G-C-Eb
    'major_arpeggio_up': [0, 4, 7, 12, 16],       # C-E-G-C-E
    'scale_run_up': [0, 2, 4, 5, 7],              # C-D-E-F-G
    'scale_run_down': [7, 5, 4, 2, 0],            # G-F-E-D-C
    'turnaround': [0, 7, 0, 11, 7],               # C-G-C-B-G
}

# Vocal chop patterns - chromatic approach and syncopated runs
# Each is a list of semitone offsets from a target note
VOCAL_CHOP_PATTERNS = {
    'chromatic_approach_up': [-1, -1, 0, 1, 0],   # B-B-C#-D-C# to target D
    'chromatic_approach_down': [1, 1, 0, -1, 0],  # D-D-C#-B-C# to target C#
    'major_arpeggio': [0, 4, 7, 12, 16],          # root-3rd-5th-octave-major3
    'minor_triad_roll': [0, 3, 7, 12, 15],        # root-min3-5th-octave-min3
    'diminished_run': [0, 3, 6, 9, 12],           # diminished arpeggio run
}

# Roman numeral to scale degree index mapping
ROMAN_TO_DEGREE = {
    'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'vi': 5, 'VII': 6,
    'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4, 'VI': 5, 'vii': 6,
}


def roman_to_degree_idx(roman: str) -> int:
    """Convert Roman numeral to scale degree index (0-6)."""
    return ROMAN_TO_DEGREE.get(roman, 0)


@dataclass
class TrackConfig:
    """Per-track configuration for generation."""
    enabled: bool = False
    velocity_min: int = 50
    velocity_max: int = 100
    octave_shift: int = 0      # -2 to +2
    complexity: float = 0.5    # 0.0 (simple) to 1.0 (complex)


@dataclass
class GenerationConfig:
    """Shared configuration for all generators."""
    root_note: str = 'C'            # e.g., "C", "A"
    scale_mode: str = 'major'      # e.g., "major", "natural_minor"
    bpm: int = 120                 # beats per minute
    bar_length: int = 8            # number of bars to generate
    seed: Optional[int] = None     # reproducibility seed
    track_configs: dict = field(default_factory=dict)  # track_name -> TrackConfig


# ----- NOTE NAME / MIDI CONVERSION -----

def get_note_name(note_number: int) -> str:
    """Convert MIDI note number to note name with octave (e.g., 60 -> 'C4')."""
    octave = note_number // 12 - 1
    note_in_octave = note_number % 12
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return f"{notes[note_in_octave]}{octave}"


def get_midi_note_from_name(note_name: str) -> int:
    """
    Convert note name (e.g., 'C4') to MIDI note number.
    If no octave given, assumes octave 4.
    """
    if not note_name:
        return 60  # Default to C4

    note = note_name.rstrip('0123456789')
    octave_str = note_name[len(note):]
    octave = int(octave_str) if octave_str else 4

    if note not in GM_NOTES:
        raise ValueError(f"Invalid note name: {note_name}")

    base_val = GM_NOTES[note]
    return (octave + 1) * 12 + (base_val - 60)


# ----- SCALE / CHORD HELPERS -----

def get_scale_notes(root_note: str, scale_mode: str) -> List[str]:
    """Get list of note names for the given root and scale mode."""
    if scale_mode not in SCALE_TABLES:
        raise ValueError(f"Unknown scale mode: {scale_mode}")

    relative_notes = SCALE_TABLES[scale_mode]
    absolute_notes = []
    for degree in relative_notes:
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
    scale_degree = roman_to_degree_idx(chord_type)
    chord_type_lower = chord_type.lower()

    if chord_type_lower not in CHORD_TEMPLATES:
        raise ValueError(f"Unknown chord type: {chord_type}")

    chord_notes = []
    for degree in CHORD_TEMPLATES[chord_type_lower]:
        abs_note = GM_NOTES[root_note] + (degree % 12)
        chord_notes.append(abs_note)

    return get_chord_name(root_note, chord_type), chord_notes


def get_chord_name(root_note: str, chord_type: str) -> str:
    """Get a Roman numeral chord name like 'IC', 'V', 'vi'."""
    # Quality indicators based on chord type
    if chord_type in ('I', 'III', 'VI', 'V'):
        quality = ''
    elif chord_type in ('i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'):
        quality = 'm'
    else:
        quality = ''
    return f"{root_note}{quality}"


def get_chord_notes_from_name(chord_name: str) -> List[int]:
    """Get MIDI note numbers for a chord name like 'Cmaj7' or 'Am7'."""
    # Parse the chord name
    parts = chord_name.split()
    root_note = parts[0]

    # Determine quality from remaining parts
    quality = ''
    if len(parts) > 1:
        quality = parts[1].lower()
        if quality in ('maj', 'major'):
            quality = 'Maj7'
        elif quality in ('min', 'minor'):
            quality = 'm7'
        elif quality in ('dim', 'half-dim'):
            quality = 'dim7'
        elif quality in ('aug', 'augmented'):
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
                                  progression_type: Optional[str] = None) -> List[str]:
    """Get a list of chord names for the given key and optional progression type."""
    if not progression_type or progression_type == 'default':
        prog_type = 'I-V-vi-IV'
    else:
        prog_type = progression_type

    chords = []
    for roman in CHORD_PROGRESSIONS[prog_type]:
        chord_name, _ = get_chord_from_scale_degree(scale_mode, roman, root_note)
        chords.append(chord_name)
    return chords


# ----- CHORD PROGRESSION COORDINATION -----

def build_chord_progression(config: GenerationConfig) -> List[Tuple[int, List[int]]]:
    """
    Build the full chord progression for the entire song.
    
    Returns:
        List of (bar_index, [midi_note1, midi_note2, midi_note3]) tuples
    """
    scale_notes_midi = get_scale_notes_midi(config.root_note, config.scale_mode)
    prog_name = 'I-V-vi-IV'
    roman_list = CHORD_PROGRESSIONS[prog_name]
    
    progression = []
    for bar in range(config.bar_length):
        if bar == 0:
            chord_idx = 0
        elif bar % 4 == 2:
            chord_idx = min(3, len(roman_list) - 1)
        else:
            chord_idx = random.randint(0, len(roman_list) - 1)
        
        roman = roman_list[chord_idx]
        degree_idx = roman_to_degree_idx(roman)
        
        if degree_idx < len(scale_notes_midi):
            root = scale_notes_midi[degree_idx]
        else:
            root = 60
        
        # Get third and fifth from scale
        third_idx = (degree_idx + 2) % 7
        fifth_idx = (degree_idx + 4) % 7
        
        third = scale_notes_midi[third_idx] if third_idx < len(scale_notes_midi) else root + 4
        fifth = scale_notes_midi[fifth_idx] if fifth_idx < len(scale_notes_midi) else root + 7
        
        # Voice in register 48-72
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
        
        progression.append((bar, [root, third, fifth]))
    
    return progression


def get_chord_at_position(bar: int, beat: float,
                          chord_progression: List[Tuple[int, List[int]]]) -> Tuple[str, List[int]]:
    """
    Get the chord name and notes for a specific bar and beat in the progression.
    
    Args:
        bar: Bar number (0-indexed)
        beat: Beat within bar (0.0-4.0)
        chord_progression: List of (bar_index, [midi_notes]) from build_chord_progression()
    
    Returns:
        Tuple of (chord_name, list_of_midi_note_numbers)
    """
    # Find the chord for this bar
    for bar_idx, notes in chord_progression:
        if bar_idx == bar:
            # Build a simple chord name from the root note
            root_name = get_note_name(notes[0])
            return root_name, notes
    
    # Fallback
    return 'C', [60, 64, 67]


# ----- REGISTER / RANGE HELPERS -----

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


def get_velocity_range(generator_type: str) -> Tuple[int, int]:
    """Get recommended velocity range for a generator type."""
    ranges = {
        'bassline': (60, 95),
        'chords': (40, 85),
        'melody': (50, 100),
        'counter_melody': (60, 100),
        'vocal_chops': (70, 110),
        'turnaround_fills': (80, 120),
        'hihats': (20, 127),
    }
    return ranges.get(generator_type, (50, 100))


# ----- MIDI FILE GENERATION -----

def generate_midi_file(config: GenerationConfig,
                       note_data: List[Tuple[int, float, int]],
                       output_path: str):
    """
    Generate a MIDI file from note data.
    
    Writes each note as a sequential note_on / note_off pair.
    The note_off delta advances the track clock, so the next
    note starts after the previous one finishes. This naturally
    fills all requested bars, matching the old version's behavior.
    
    For chord tracks: notes from the same chord play as a fast
    arpeggio (sequential), not as a simultaneous block. This is
    a known trade-off that produces correctly-timed, full-length
    MIDI files suitable for LMMS import.
    
    Args:
        config: Generation configuration (bpm, etc.)
        note_data: List of (pitch, duration_seconds, velocity) tuples
        output_path: Path to save the .mid file
    """
    from mido import MidiFile, MidiTrack, MetaMessage, Message

    # Create new MIDI file (Type 1 - single track)
    midi = MidiFile(type=1)
    track = MidiTrack()
    midi.tracks.append(track)

    # Set tempo meta event: tempo is microseconds per beat
    tempo_us_per_beat = int(60_000_000 / config.bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo_us_per_beat))

    # Default ticks per beat in mido is 480
    ticks_per_beat = 480
    seconds_per_tick = 60.0 / (config.bpm * ticks_per_beat)

    # Write each note as a sequential note_on / note_off pair.
    # Each note_off's delta time advances the track clock to the
    # next note's start position, producing correct multi-bar output.
    for pitch, duration_sec, velocity in note_data:
        duration_ticks = int(duration_sec / seconds_per_tick) if seconds_per_tick > 0 else 1
        # Note on — time=0 (starts immediately after previous event)
        track.append(Message('note_on', note=pitch, velocity=velocity, time=0))
        # Note off — delta advances clock by the note's duration
        track.append(Message('note_off', note=pitch, velocity=0, time=duration_ticks))

    # End of track marker
    track.append(MetaMessage('end_of_track', time=0))

    # Save the MIDI file
    midi.save(output_path)


# Backward-compatible wrapper for old-style note_data (pitch, duration) without velocity
def generate_midi_file_old(config: GenerationConfig,
                           note_data: List[Tuple[int, float]],
                           output_path: str,
                           velocity: int = 80):
    """Legacy wrapper that converts (pitch, duration) tuples to include velocity."""
    new_data = [(p, d, velocity) for p, d in note_data]
    generate_midi_file(config, new_data, output_path)