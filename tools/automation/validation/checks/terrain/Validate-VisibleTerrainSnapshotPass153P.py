#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[5]
terrain = root / "crates/haven_game/src/runtime_terrain_pass.rs"
main = root / "crates/haven_game/src/main.rs"
runtime_draw = root / "crates/haven_game/src/runtime_draw.rs"
client_entry = root / "crates/haven_game/src/runtime_performance_snapshot.rs"

for path in (terrain, main, runtime_draw, client_entry):
    if not path.exists():
        raise SystemExit(f"Pass 153P missing {path.relative_to(root)}")

text = terrain.read_text(encoding="utf-8")
required = [
    "struct VisibleTerrainCell<'a>",
    "resolved_group: Option<TileAutoGroup>",
    "transitions: Option<&'a ResolvedTerrainTransitions>",
    "water_mask: Option<WaterRenderMask>",
    "cell.transitions",
    "cell.water_mask",
    "resolved_base: Option<(TileAutoGroup, u8)>",
]
for token in required:
    if token not in text:
        raise SystemExit(f"Pass 153P missing {token!r} in runtime_terrain_pass.rs")

lookup_count = (
    text.count("self.terrain_cache.resolved_at(")
    + text.count("base_terrain_cache.record_at(")
    + text.count("base_terrain_cache.for_each_visible_record(")
)
if lookup_count != 1:
    raise SystemExit("Pass 153P expected exactly one retained terrain access path in visible preparation")
if "Pass 155B" not in (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8"):
    raise SystemExit("Pass 153 runtime HUD identifier missing")
if "PERF_SNAPSHOT pass=" not in client_entry.read_text(encoding="utf-8"):
    raise SystemExit("Pass 153 performance snapshot identifier missing")

print("Pass 153P OK: one visible-cell snapshot carries cached autotile, transition, and water data through all terrain passes")
