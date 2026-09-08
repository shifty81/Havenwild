# Pass 121 — Shore/Water Normalization

Date: 2026-07-15

## Purpose

This pass starts enforcing the terrain contract from Pass120 in the live editor.

It focuses on local edits only. Full-map worldgen coastline cleanup remains owned by the existing world coastline pass.

## Rules enforced after editor tile paint/erase/context-paint

- Sand touching water becomes wet sand.
- Wet sand away from water normalizes back to sand.
- Deep water touching land/shore becomes shallow water.
- Shallow water fully surrounded by water can promote to deep water.

## Why

Wet sand is generated shore terrain, not a normal inland paint material. Deep water should not directly touch land. These two rules address the visible beach/water artifacts while preserving the semantic tile model.

## Guard

`tools/automation/validation/checks/terrain/Validate-ShoreWaterNormalizationV127.py` checks that the editor helper, unit-test coverage, terrain registry contract, and build wiring remain in place.

## Next pass

Pass122 should address path/ground pair coverage:

- mountain_path ↔ sand/dirt/grass
- stone_path ↔ sand/dirt/grass
- pebble_shore ↔ sand/dirt/wet_sand
- stone_path and pebble_shore semantic split
