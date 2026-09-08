#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "crates/haven_game/src/terrain_transition_draw.rs"

def fail(message: str) -> None:
    raise SystemExit(f"Pass 167Z57 validation failed: {message}")

text = SOURCE.read_text(encoding="utf-8")

retired = [
    "supports_direct_lpc_transition",
    "fn diagonal(self)",
    "fn cardinals(self)",
    "fn transition_group_priority",
    "fn edge_group(",
    "fn inner_group(",
    "fn quadrant_source(",
    "fn quadrant_source_group",
    "ResolvedTerrainTransitions",
    "transition_pair_atlas_group",
]
for marker in retired:
    if marker in text:
        fail(f"retired generic transition marker remains: {marker}")

required = [
    "pub(crate) fn draw_direct_water_depth_rim",
    "WaterRenderMask",
    "fn depth_outer_cell",
    "fn draw_full_depth_cell",
    "fn draw_depth_inner_corners",
    "fn draw_quadrant_source",
    '"shallow_rim_over_deep"',
]
for marker in required:
    if marker not in text:
        fail(f"active water-depth renderer marker missing: {marker}")

for suppression in ["allow(dead_code)", "expect(dead_code)"]:
    if suppression in text:
        fail(f"dead-code suppression is not permitted: {suppression}")

print("Pass 167Z57 water-depth renderer Clippy cleanup validated")
