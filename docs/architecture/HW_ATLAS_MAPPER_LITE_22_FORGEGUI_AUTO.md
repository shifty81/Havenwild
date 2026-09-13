# HW-ATLAS-MAPPER-LITE-FORGEGUI-AUTO-22

This pass moves Atlas Mapper Lite from a prototype canvas into the Havenwild asset-intake tile-sheet lane.

## Goals

- Give the mapper a more professional Forge-style GUI treatment.
- Keep the source atlas immutable.
- Keep the assembly canvas readable by clamping zoom to 100% or higher.
- Add a category-aware **Auto Map** path for quickly seeding an assembly from a loaded sheet.
- Add visible mapped/unmapped status beside the loaded tile sheet.
- Write mapped-sheet records into `artifacts/asset-intake/atlas-mapper/mapped-sheets` so the future asset library browser can show green checkmarks beside mapped sheets.
- Normalize the launcher into the internal PCC Run and Asset Authority menus.

## What changed

### GUI

The mapper now uses a three-panel layout:

1. **Source Tile Sheet** — immutable source atlas with 32×32 selection.
2. **Assembly Canvas** — puzzle-piece composition surface.
3. **Asset Intake** — category, mapped state, Auto Map, Save Project, Export Handoff, and next-step guidance.

The style is intentionally closer to the Forge GUI direction: dark panel surfaces, header bands, status pills, better borders, and a stable bottom status strip.

### Auto Map

`Auto Map` and `Ctrl+G` seed the canvas using the current asset category. This is not final certification; it is a fast starting point for review.

The auto-layout categories are:

- Terrain
- Cliff
- Structure
- House
- Object
- Character
- Equipment
- FX
- UI

### Mapped sheet status

A loaded sheet now shows:

- `UNMAPPED` when there is no mapper evidence yet.
- `MAPPED DRAFT`, `PROJECT SAVED`, or `HANDOFF EXPORTED` once mapping evidence exists.

Green mapped state means the sheet has mapper metadata. It does **not** mean the asset is runtime-published.

### PCC menu integration

The mapper command is registered as:

```text
Atlas Mapper Lite / Tile Sheet Mapper
```

It appears in both:

```text
4. Run & play
6. Asset authority & catalog
```

## Next required passes

1. Add catalog-backed library browsing using `content/assets/lpc/lpc_slice_catalog_v0_1.json` and registered external roots.
2. Show green checkmarks beside every mapped sheet row in the library browser.
3. Add socket/edge annotation.
4. Add footprint/collision/depth annotation.
5. Add importer from mapper handoff into Asset Authority candidates.
6. Audit the full Havenwild editor and migrate Forge GUI treatments into the main GameMaker-style infinite-canvas shell.
