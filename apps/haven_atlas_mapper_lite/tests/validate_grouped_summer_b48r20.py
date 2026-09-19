#!/usr/bin/env python3
"""Offline grouped Summer GUI contract; only the Windows GUI/build can certify behavior."""
from pathlib import Path
import argparse, sys
p = argparse.ArgumentParser()
p.add_argument('--repo', default='.')
root = Path(p.parse_args().repo).resolve()
s = (root/'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
checks = {
    'Summer source groups': all(k in s for k in ['enum SourceGroup', 'Self::Ground', 'Self::Water', 'Self::Cliffs', 'Self::Furniture', 'Self::Characters']),
    'subject-specific furniture grouping': 'name.contains(word)) { Self::Furniture }' in s and 'file.contains(word)) { AssetCategory::Object }' in s,
    'filtered library retains active sources': 'self.sheet_library_group.map_or(true' in s and 'self.sheet_library_visible = self.sheet_library.iter()' in s,
    'group buttons clickable': 'app.sheet_library_group = group;' in s and 'app.rebuild_sheet_library_visibility();' in s,
    'group controls excluded from card input': 'mouse.y < stack.y + SHEET_LIST_TOP' in s,
    'source stack scrolling matches list geometry': 'visible_h = (source_sheet_stack_rect(source_rect).h - SHEET_LIST_TOP)' in s,
    'inactive category nav removed': 'for category in AssetCategory::ALL {' not in s[s.index('fn draw_top_bar'):s.index('fn draw_source_panel')],
    'nonfunctional tabs removed': 'draw_dock_tabs(inspector_rect' not in s and 'draw_dock_tabs(canvas_rect' not in s,
    'startup demo is real saved project': 'fn save_startup_summer_demo' in s and 'if demo.is_file() { app.load_project(&demo); }' in s,
    'no fabricated demo geometry': 'The B48R7 fixture' in (root/'apps/haven_atlas_mapper_lite/README.md').read_text(encoding='utf-8'),
    'reassemble honestly labelled': 'Recipe-driven reroll is NOT implemented.' in s and 'Stage missing cells' in s,
    'approval remains guarded': 'let complete = mapped_tile_count > 0 && coverage_percent >= 99.999 && all_approved' in s,
    'real elevation +1 remains valid': 'cell.elevation > 30' in s and 'water_surface.is_some_and(|water| water > 30)' in s,
}
for label, ok in checks.items(): print(('PASS' if ok else 'FAIL') + ': ' + label)
if not all(checks.values()): sys.exit(1)
print('PASS grouped Summer static checks; native Rust/GUI NOT VERIFIED')
