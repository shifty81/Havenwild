#!/usr/bin/env python3
"""B48R23 source-level regression. Not a substitute for native GUI or PCC gate."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--repo', default='.')
root = Path(parser.parse_args().repo).resolve()
s = (root / 'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf8')
checks = {
    'recognizable mapper build marker': any(marker in s for marker in ('B48R23 source-library / erase repair', 'B48R24 unified library / editable scene layers')),
    'standalone executable discovers repository root': 'fn discover_havenwild_root()' in s and 'env::current_exe()' in s and 'env::set_current_dir(&root)' in s,
    'clear no-asset diagnostic includes discovered directory': 'NO ELIZAWY SHEETS FOUND. Root:' in s and 'app.library_notice' in s,
    'original sheets indexed without eager texture activation': 'self.collect_sheet_cards(&root, &scan_root' in s and 'Textures load only when activated' in s,
    'characters excluded from Summer browser, model retained': 'normalized.contains("/characters/")' in s and 'Self::Characters => "Characters"' in s and 'lpc_revised/Characters"),' not in s,
    'larger atlas and source-list toggle': 'atlas_focus: true' in s and '"More library"' in s and '"Larger atlas"' in s,
    'delete keyboard, right click and visible button share one implementation': s.count('self.remove_selected_piece();') >= 2 and 'app.remove_selected_piece();' in s and 'MouseButton::Right' in s,
    'deletion checkpoints, clears stale handoff, marks dirty, preserves heights': 'let removed = self.pieces.remove(index);' in s and 'self.checkpoint_scene();' in s and 'self.last_handoff_path = None;' in s and 'Height/water data preserved.' in s,
    'first row no longer tucked under toolbar': 'canvas_pan: vec2(56.0, 116.0)' in s and 'self.canvas_pan = vec2(56.0, 116.0);' in s,
    'no fabricated recipe generator or automatic approval': 'No recipe reroll yet; candidate only.' in s and 'MAPPED_TILE_STATUS_APPROVED' in s,
}
for label, ok in checks.items(): print(('PASS' if ok else 'FAIL') + ': ' + label)
assert all(checks.values()), 'B48R23 mapper regression failed'
original = root / 'assets/source/licensed/lpc_revised'
if original.is_dir():
    sources = [p for p in original.rglob('*.png') if '/characters/' not in p.as_posix().lower() and '/character/' not in p.as_posix().lower()]
    assert sources and any('summer' in p.name.lower() for p in sources), 'No Summer source PNGs available'
    print(f'PASS: {len(sources)} original non-character PNGs present in cumulative source overlay (availability, not semantic certification)')
else:
    print('NOTE: source PNG root unavailable in this checkout; file availability test skipped')
print('PASS: B48R23 static boot/erase contract. Native Rust GUI, live root scan and PCC gate still require Windows.')
