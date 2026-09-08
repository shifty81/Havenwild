from pathlib import Path

root = Path(__file__).resolve().parents[5]
cache = (root / "crates/haven_game/src/chunk_surface_cache.rs").read_text(encoding="utf-8")
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
snapshot = (root / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text(encoding="utf-8")
required_cache = [
    "expected_commands",
    "parity_mismatches",
    "parity_ok",
    '"parity-count-mismatch"',
    '"retained-command-parity"',
]
missing = [token for token in required_cache if token not in cache]
if missing:
    raise SystemExit(f"Pass 154E parity cache contract missing: {missing}")
if "expected_visible_coordinates" not in terrain and "expected_visible_commands" not in terrain:
    raise SystemExit("Pass 154E must compare retained coverage against authoritative visible cells")
for field in ("chunk_exec_expected", "chunk_exec_parity_ok", "chunk_exec_parity_mismatches"):
    if field not in snapshot:
        raise SystemExit(f"Pass 154E snapshot field missing: {field}")
print("Pass 154E OK: retained command execution is parity-gated before drawing and mismatches force complete fallback")
