#!/usr/bin/env python3
from pathlib import Path
import re
root = Path(__file__).resolve().parents[5]
issues = []
asset_panel = root / 'crates/haven_game/src/asset_reference_browser_panel.rs'
commands = root / 'crates/haven_game/src/runtime_commands.rs'
main = root / 'crates/haven_game/src/main.rs'

asset_text = asset_panel.read_text(encoding='utf-8')
if 'let row = rows[absolute];' in asset_text:
    issues.append('asset_reference_browser_panel.rs still moves rows[absolute] instead of borrowing it')
if 'let row = &rows[absolute];' not in asset_text:
    issues.append('asset_reference_browser_panel.rs missing borrowed selected asset row')

cmd_text = commands.read_text(encoding='utf-8')
for tab in ['EditorTab::Paint', 'EditorTab::Transitions', 'EditorTab::Assets']:
    if tab not in cmd_text:
        issues.append(f'runtime_commands.rs missing match arm for {tab}')
if 'EditorTab::Paint => EditorCommandKind::PaintTerrain' not in cmd_text:
    issues.append('Paint tab should map to PaintTerrain editor command kind')
if 'EditorTab::Transitions => EditorCommandKind::CreateTransition' not in cmd_text:
    issues.append('Transitions tab should map to CreateTransition editor command kind')
if 'EditorTab::Assets => EditorCommandKind::SceneMutation' not in cmd_text:
    issues.append('Assets tab should map to SceneMutation editor command kind')

main_text = main.read_text(encoding='utf-8')
if 'resolve_world_paint_scene_transition_tile_details' in main_text:
    issues.append('main.rs still imports unused resolve_world_paint_scene_transition_tile_details')

if issues:
    print('Validate-GameCompileHotfixV48 FAILED')
    for issue in issues:
        print(' -', issue)
    raise SystemExit(1)
print('Validate-GameCompileHotfixV48 passed')
