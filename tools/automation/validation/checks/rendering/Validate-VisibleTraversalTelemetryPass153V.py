from pathlib import Path
root = Path(__file__).resolve().parents[5]
base = (root/'crates/haven_game/src/base_terrain_cache.rs').read_text()
tele = (root/'crates/haven_game/src/render_telemetry.rs').read_text()
entry = (root/'crates/haven_game/src/runtime_performance_snapshot.rs').read_text()
diag = (root/'crates/haven_game/src/runtime_diagnostics.rs').read_text()
required = ['visible_cache_hits', 'visible_cache_rebuilds', 'visible_cache_last_reason', 'visible_cached_cells']
missing = [m for m in required if m not in base]
if missing:
    raise SystemExit('Pass 153V missing traversal telemetry markers: ' + ', '.join(missing))
for marker in ['traversal_hits=', 'traversal_rebuilds=', 'traversal_reason=', 'PERF_SNAPSHOT pass=']:
    if marker not in entry:
        raise SystemExit('Pass 153V structured snapshot missing ' + marker)
if 'Pass 155B' not in diag or 'traversal_summary' not in diag:
    raise SystemExit('Pass 153V HUD diagnostics missing traversal summary')
if 'visible_cache_hits' not in tele or 'visible_cache_reason' not in tele:
    raise SystemExit('Pass 153V telemetry forwarding missing')
print('Pass 153V OK: visible traversal cache hits, rebuilds, reused cells, and invalidation reasons are exposed')
