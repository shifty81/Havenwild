from pathlib import Path

root = Path(__file__).resolve().parents[5]
cache = (root / "crates/haven_game/src/chunk_surface_cache.rs").read_text(encoding="utf-8")
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
snapshot = (root / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text(encoding="utf-8")
required = [
    "expected_coordinates: &[(i32, i32)]",
    "BTreeSet<(i32, i32)>",
    "duplicate_commands",
    "missing_coordinates",
    "unexpected_coordinates",
    '"parity-duplicate-command"',
    '"parity-coordinate-mismatch"',
    "duplicate_coordinate_forces_safe_fallback_even_when_count_matches",
    "shifted_coordinate_forces_coordinate_fallback",
]
missing = [item for item in required if item not in cache]
if "expected_visible_coordinates" not in terrain:
    missing.append("runtime expected coordinate coverage")
for field in ["chunk_exec_unique", "chunk_exec_duplicates", "chunk_exec_missing", "chunk_exec_unexpected"]:
    if field not in snapshot:
        missing.append(field)
if missing:
    raise SystemExit("Pass 154F validation failed: " + ", ".join(missing))
print("Pass 154F retained command exact-coordinate parity validation passed.")
