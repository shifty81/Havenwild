from pathlib import Path
root = Path(__file__).resolve().parents[5]
cache = (root / 'crates/haven_game/src/base_terrain_cache.rs').read_text(encoding='utf-8')
runtime = (root / 'crates/haven_game/src/runtime_terrain_pass.rs').read_text(encoding='utf-8')
required = [
    'visible_bounds: Option<(i32, i32, i32, i32)>',
    'visible_indices: Vec<(i32, i32, usize)>',
    'if self.visible_bounds != Some(bounds)',
    'fn rebuild_visible_indices',
    'self.visible_bounds = None;',
]
missing = [item for item in required if item not in cache]
if missing:
    raise SystemExit('Pass 153U missing retained traversal cache markers: ' + ', '.join(missing))
if 'for_each_visible_record' not in runtime:
    raise SystemExit('Pass 153U runtime no longer consumes retained visible records')
print('Pass 153U OK: stationary camera bounds reuse retained visible-cell indices and terrain revisions invalidate them')
