"""Quick test of fit checker against generated files."""
import os, sys
sys.path.insert(0, '.')

from analysis.fit_checker import check_all_tracks
from generators.common import GenerationConfig

config = GenerationConfig(root_note='C', scale_mode='major', bpm=140, bar_length=64, seed=1813348037)

midi_files = {}
for name in ['chords', 'bassline', 'hihats', 'melody', 'countermelody', 'vocal_chops', 'turnaround_fills']:
    path = f'OUTPUT_DEV/{name}.mid'
    if os.path.exists(path):
        # Map to the display names used by main_window
        display = name.replace('_', ' ').title().replace('Chords', 'Chords').replace('Countermelody', 'Counter-Melody')
        if name == 'countermelody':
            display = 'Counter-Melody'
        midi_files[display] = path
        print(f"Found: {display} -> {path}")

print(f"\nRunning fit check with {len(midi_files)} tracks...")
result = check_all_tracks(config, midi_files)

print(f"\nScore: {result['overall_score']}/100")
print(f"Passed: {result['passed']}")
print(f"Total issues: {len(result['issues'])}")
print(f"\nFirst 30 issues:")
for i, issue in enumerate(result['issues'][:30]):
    print(f"  {i+1}. {issue}")

if len(result['issues']) > 30:
    print(f"  ... ({len(result['issues']) - 30} more)")