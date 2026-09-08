# Pass 135 — terrain-v7 editor exposure and water-adjacent paint guards

## Scope

- Expose every currently mapped terrain-map-v7 semantic terrain tile in the in-game terrain editor.
- Keep structural cliff and mountain rock deferred from the terrain-v7 ground tuple editor until dedicated structural topology is mapped.
- Badge editor terrain thumbnails by authoring state instead of hiding generated/overlay terrain semantics.
- Make F3 a true editor toggle: F3 opens the editor and F3 closes/saves it.
- Strengthen local editor shore/water normalization for land, sand, pebble shore, road, and path painting over or near water.
- Force deep-water/land mixed tuples through stable shore fallback fills instead of allowing stale exact tuples to reintroduce square legacy artifacts.

## Current tuple state

The terrain-v7 tuple coverage audit remains the source of truth:

- 1,536 total material/pattern combinations resolve.
- 906 are exact authored tuples.
- 630 use guarded terrain-v7 fallback fills.
- 0 are missing.

This means every current tuple can render through the mapped terrain-v7 path, but not every tuple is promoted to exact authored art yet. Fallback-heavy rows should still be promoted in later passes using the tuple promotion plan.

## Editor terrain exposed

The in-game terrain editor now exposes the mapped semantic terrain set:

- Grass
- Tall Grass
- Dirt
- Sand
- Wet Sand
- Pebble Shore
- Road
- Stone Path
- Mountain Path
- Cave Floor
- Tilled Soil
- Watered Soil
- Water
- Shallow Water
- Deep Water
- Deep Ocean
- Shallow Ocean
- River Water
- River Mouth Blend
- Shore Foam
- Mud Bank

Badges distinguish production, generated, overlay, and preview semantics.

## Deferred

- Cliff and Mountain Rock remain excluded from terrain-v7 ground tuple painting because their current source roles behave like structural rock/cliff topology, not ordinary ground blends.
- Full exact tuple promotion remains separate from tuple visibility/resolution. The promotion plan should be used to replace fallback-heavy rows with authored exact mappings.
