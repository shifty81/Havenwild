# Pass 117 — Structural Rock Terrain Deferral

Date: 2026-07-15

## What changed

- `cliff` and `mountain_rock` no longer route through the complete LPC ground-corner terrain atlas.
- The mapped terrain atlas now exports only natural ground/water/floor materials that have valid complete-tile corner topology.
- Added `Validate-LpcStructuralRockTerrainDeferralV125.py` so the build fails if cliff or mountain rock are reintroduced into the ground atlas before dedicated structural rock topology exists.

## Why

`Rock_Gray` and `Rock_Dark` in `lpc-terrains-v7` are cave/rock ground materials. They are not cliff-face or mountain-wall topology. Using them as universal ground-corner materials caused cliff/mountain-rock brushes to pick unrelated border art, including water/coast-looking edges.

## Current terrain contract

- Grass, sand, dirt, paths, pebble shore aliases, farm soil, cave floor, and water families may use the complete mapped terrain atlas.
- Wet sand remains deferred until a true dry wet-sand material is mapped.
- Cliff and mountain rock remain structural terrain. They need their own topology pass rather than generic four-corner ground blending.

## Next terrain/editor work

1. Add a terrain variation/density control for deterministic fill variants:
   - none/base only
   - low detail
   - normal detail
   - high detail
2. Expose material variants in the editor as thumbnail-backed brush choices without exploding the core `TileKind` enum.
3. Build dedicated water-depth rules:
   - deep water owns open interiors
   - shallow water rings land/shore
   - no square fallback detail patches in open water
4. Build dedicated cliff/mountain-rock topology:
   - cliff face/wall edges
   - rock caps/floors
   - grass/sand/dirt contact rules
5. Normalize beach materials so pure sand, wet sand, shallow water, shore foam, and pebble shore do not fight each other visually.
