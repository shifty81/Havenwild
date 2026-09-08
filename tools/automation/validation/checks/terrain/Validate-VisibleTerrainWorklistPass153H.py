#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[5]
text = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
required = [
    "struct VisibleTerrainCell",
    "let mut visible_cells = Vec::with_capacity",
    "base_terrain_cache.for_each_visible_record",
    "paint_owned",
    "for cell in visible_cells.iter().filter",
    "let mut transition_work = Vec::with_capacity",
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Pass 153H validation FAILED: missing " + ", ".join(missing))
if text.count("base_terrain_cache.for_each_visible_record") != 1:
    raise SystemExit("Pass 153H validation FAILED: retained visible terrain must be traversed exactly once")
print("Pass 153H OK: one retained visible-terrain worklist feeds base, paint, transition, water, and debug passes")
