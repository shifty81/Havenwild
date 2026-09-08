#!/usr/bin/env python3
"""
Validate the Havenwild coastline cleanup pass.

This is intentionally source-structure-aware rather than cargo-dependent so it
can run in lightweight handoff/sandbox environments where Rust is unavailable.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "logs/coastline_cleanup_v12_validation_report.json"

checks: list[dict[str, str]] = []
errors: list[str] = []
warnings: list[str] = []

def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def require_contains(rel: str, needle: str) -> None:
    text = read(rel)
    name = f"contains:{rel}:{needle}"
    if needle in text:
        checks.append({"name": name, "status": "ok"})
    else:
        errors.append(f"{rel} does not contain expected text: {needle}")

def require_json_value(rel: str, path: list[str], expected) -> None:
    text = read(rel)
    if not text:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{rel} is not valid JSON: {exc}")
        return
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            errors.append(f"{rel} missing JSON path: {'.'.join(path)}")
            return
        current = current[key]
    if current == expected:
        checks.append({"name": f"json:{rel}:{'.'.join(path)}", "status": "ok"})
    else:
        errors.append(f"{rel} JSON path {'.'.join(path)} expected {expected!r}, got {current!r}")

require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "pub struct CoastlineCleanupReport",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "smooth_tiny_coast_artifacts",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "removed_water_speckles",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "eroded_land_spikes",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "shallow_water_band_tiles",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "primary_shore_tile",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "secondary_shore_tile",
)
require_contains(
    "crates/haven_world/src/autotile/shoreline_resolver.rs",
    "authored_farm_tiles_are_not_erased_by_coast_cleanup",
)
require_contains(
    "crates/haven_world/src/autotile/mod.rs",
    "CoastlineCleanupReport",
)
require_contains(
    "crates/haven_game/src/main.rs",
    "apply_generated_coastline_cleanup",
)
require_contains(
    "crates/haven_game/src/main.rs",
    "Saved worlds are intentionally not auto-mutated",
)
require_contains(
    "crates/haven_game/src/runtime_scene_navigation.rs",
    "apply_coastline_tile_pass(&mut replacement.map, replacement.biome)",
)
require_contains(
    "crates/haven_core/src/foundation.rs",
    "SceneId::Farmstead => SceneBiome::Coastal",
)
require_json_value(
    "content/worldgen/havenwild_open_world_preset_v1.json",
    ["coastline_cleanup", "enabled"],
    True,
)
require_json_value(
    "content/worldgen/havenwild_open_world_preset_v1.json",
    ["coastline_cleanup", "preserveAuthoredTiles"],
    True,
)

preset_text = read("content/worldgen/havenwild_open_world_preset_v1.json")
if "coastline_cleanup_and_transition_bake" in preset_text:
    checks.append({"name": "generation stage includes coastline cleanup", "status": "ok"})
else:
    errors.append("open world preset generation_stages missing coastline_cleanup_and_transition_bake")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps({"checks": checks, "errors": errors, "warnings": warnings}, indent=2),
    encoding="utf-8",
)

if errors:
    print(f"Coastline cleanup validation FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
    for error in errors:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print(f"Coastline cleanup validation passed: {len(checks)} checks, {len(warnings)} warning(s)")
