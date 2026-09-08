#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
telemetry = (ROOT / 'crates/haven_game/src/render_telemetry.rs').read_text(encoding='utf-8')
entry = (ROOT / 'crates/haven_game/src/client_entry.rs').read_text(encoding='utf-8')
draw = (ROOT / 'crates/haven_game/src/runtime_draw.rs').read_text(encoding='utf-8')

required_telemetry = [
    'wall_frame_micros',
    'presentation_gap_micros',
    'smoothed_wall_frame_micros',
    'wall_micros.saturating_sub(frame_micros)',
    'pub(crate) fn bottleneck_label',
    '"cpu-submit"',
    '"gpu/present"',
]
for token in required_telemetry:
    assert token in telemetry, f'missing presentation telemetry token: {token}'

assert 'next_frame().await;\n            let wall_frame_seconds' in entry, (
    'wall duration must be measured after next_frame returns'
)
assert 'submitted_frame_seconds,\n                wall_frame_seconds,' in entry
assert 'V7 authority' in (ROOT / 'crates/haven_game/src/runtime_diagnostics.rs').read_text(encoding='utf-8')
diag = (ROOT / 'crates/haven_game/src/runtime_diagnostics.rs').read_text(encoding='utf-8')
assert 'ms present [{}]' in diag
assert 'presentation_gap_millis()' in draw or 'presentation_gap_millis()' in (ROOT / 'crates/haven_game/src/runtime_performance_snapshot.rs').read_text(encoding='utf-8')
assert 'bottleneck_label()' in draw or 'bottleneck_label()' in (ROOT / 'crates/haven_game/src/runtime_performance_snapshot.rs').read_text(encoding='utf-8')

print('Pass 153L OK: wall-frame and presentation-gap profiling distinguish CPU submission from GPU/present wait')
