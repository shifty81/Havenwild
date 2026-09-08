from pathlib import Path
import sys
root = Path(__file__).resolve().parents[5]
checks = []
asset = (root / 'crates/haven_game/src/asset_reference_browser_panel.rs').read_text(encoding='utf-8')
commands = (root / 'crates/haven_game/src/runtime_commands.rs').read_text(encoding='utf-8')
main = (root / 'crates/haven_game/src/main.rs').read_text(encoding='utf-8')
tools = (root / 'crates/haven_tools/src/lib.rs').read_text(encoding='utf-8')
checks.append(('asset browser borrows donor row', 'let row = &rows[absolute];' in asset and 'let row = rows[absolute];' not in asset))
for tab in ['EditorTab::Paint', 'EditorTab::Transitions', 'EditorTab::Assets']:
    checks.append((f'runtime_commands handles {tab}', tab in commands))
checks.append(('stale game import removed', 'resolve_world_paint_scene_transition_tile_details' not in main))
checks.append(('haven_tools glob exports removed', 'pub use haven_assets::*' not in tools and 'pub use haven_world::*' not in tools and 'pub use haven_editor::*' not in tools))
failed = [name for name, ok in checks if not ok]
if failed:
    print('Recurring compile fix validation failed:')
    for name in failed:
        print(' -', name)
    sys.exit(1)
print('Recurring compile fix validation passed.')
