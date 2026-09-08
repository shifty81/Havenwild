from pathlib import Path

root = Path(__file__).resolve().parents[5]
main = (root / 'crates/haven_game/src/main.rs').read_text(encoding='utf-8')
draw_path = root / 'crates/haven_game/src/runtime_draw.rs'
draw = draw_path.read_text(encoding='utf-8')
diag = (root / 'crates/haven_game/src/runtime_diagnostics.rs').read_text(encoding='utf-8')

assert 'mod runtime_diagnostics;' in main, 'runtime diagnostics module is not registered'
assert 'format_runtime_diagnostics' in draw, 'runtime draw does not delegate diagnostics formatting'
assert 'RuntimeDiagnosticsLine' in diag, 'diagnostics input contract missing'
assert 'Pass 155B' in diag, 'current Pass 153 identifier missing from diagnostics module'
assert len(draw.splitlines()) <= 750, 'runtime_draw.rs exceeds 750-line architecture ceiling'
assert 'Pass 153S | V7 authority' not in draw, 'obsolete inline diagnostics string remains in runtime_draw.rs'
print('Pass 153T OK: retained-chunk HUD diagnostics are formatted outside runtime_draw.rs')
