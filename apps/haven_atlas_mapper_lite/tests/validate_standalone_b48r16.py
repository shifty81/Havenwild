#!/usr/bin/env python3
"""Targeted source/transport assertions. Not a Rust compilation or GUI test."""
import argparse
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, default=Path.cwd())
args = p.parse_args()
root = args.repo.resolve()
mapper = (root/'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
audit = (root/'apps/haven_atlas_mapper_lite/src/scene_audit.rs').read_text(encoding='utf-8')
ticket = (root/'tools/control/PccRestartTicket.ps1').read_text(encoding='utf-8-sig')
checks = {
    'PCC restart uses nonreserved variable': '$replacementHostScript=Join-Path' in ticket and '-f $replacementHostScript' in ticket and '$host=Join-Path' not in ticket,
    'project preflight before scene teardown': mapper.index('let mut dimensions = BTreeMap::new();') < mapper.index('self.source_stack.clear();\n        self.atlas = None;'),
    'project preflight checks duplicate ids and image decode': 'duplicate/empty source identity' in mapper and 'image::image_dimensions' in mapper and 'invalid/duplicate piece' in mapper,
    'project preflight preserves valid 0..30 and real +1': 'invalid elevation outside real 0..30' in mapper and 'level.min(30)' in mapper,
    'undo and redo capture placements and elevation': 'struct SceneSnapshot' in mapper and 'pieces: self.pieces.clone(), heightmap: self.heightmap.clone()' in mapper and 'MAX_UNDO_STEPS: usize = 64' in mapper,
    'undo save state stays dirty': 'An undo is not evidence that the last saved file is identical' in mapper,
    'undo drops after source unload': 'Cannot resurrect pieces from an unloaded source' in mapper,
    'Ctrl+Z / Ctrl+Y / visible toolbar': 'KeyCode::Z' in mapper and 'KeyCode::Y' in mapper and '"Undo", false' in mapper and '"Redo", false' in mapper,
    'canvas editing excludes UI toolbar/footer': 'fn canvas_edit_rect' in mapper and 'let edit_canvas = canvas_edit_rect(canvas_rect).contains(mouse);' in mapper and 'self.is_painting_height &&' in mapper,
    'source picker still separate from scene': 'LEFT | ElizaWy Summer Source Library' in mapper and 'RIGHT | ElizaWy Summer Scene Workspace' in mapper,
    'native audit has no approval shortcut': 'unreviewed_candidate_no_runtime_publication' in audit and 'height_boundary_recipe_pending' in audit and 'hydrology_recipe_pending' in audit,
    'native audit recognizes +1 and +30': 'one_level_ocean_facing_cliff_is_a_real_boundary_not_an_error' in audit and 'elevation: 30' in audit,
    'audit wired to UI': 'mod scene_audit;' in mapper and 'fn export_scene_audit' in mapper and '"Audit", false' in mapper,
}
for label, passed in checks.items():
    print(('PASS' if passed else 'FAIL') + ' ' + label)
if not all(checks.values()): sys.exit(1)
print('PASS B48R16 focused static guards; native Rust tests, Windows PCC and GUI STILL PENDING')
