# Havenwild vs. Godot Terrain Matrix — Pass 147R

| Havenwild current system | Godot reference concept | Finding | Required action |
|---|---|---|---|
| `TileKind` | terrain/custom-data identity | Useful semantic source, but visual families collapse distinct materials | Keep semantic IDs; derive separate terrain IDs |
| `TileAutoGroup` | terrain set | `Road`, `StonePath`, `MountainPath`, and `Bridge` share connectivity | Replace as authoritative identity |
| `TerrainFamily` | terrain ID | `StonePath -> PebblePath`; `MountainPath/Bridge -> Road` | Split identities before matching |
| `AutotileShape` cardinal mask | sides-only peering pattern | Useful for simple paths, insufficient for mixed terrain | Retain as optimization, not full pattern model |
| transition overlays | complete terrain candidate | Multiple systems can own one boundary | Move ownership into one selected pattern/layer contract |
| exact LPC tuple map | atlas candidate registry | Strong asset inventory, weak semantic pattern metadata | Normalize entries into pattern candidates |
| shoreline lifecycle | gameplay/PCG normalization | Mutates logical terrain and can react badly to path painting | Run before visual matching; never use to repair invalid ordinary path placement |
| F3 paint | Connect/Path/manual painter | Direct cell mutation lacks stroke intent and feasibility checks | Route through shared placement request |
| PCG coastline | terrain-region generation | Grass/water work because regions are broad and covered | Add feasibility gate before roads/paths/details |
| manual autotile override | manual tile selection | Stores group/mask rather than stable authored candidate | Expand to pattern/source/coord/alternative ID |
| dirty 3×3 cells | local terrain update | Correct basic strategy | Keep; expand to stroke-union dirty region |
| render layers | multiple TileMapLayer nodes | Ownership is implicit and overlapping | Define base/path/transition/shore/water/detail layers |

## Confirmed identity collisions

- `TileKind::StonePath` becomes `TerrainFamily::PebblePath`.
- `TileKind::MountainPath` becomes `TerrainFamily::Road`.
- `TileKind::Bridge` becomes `TerrainFamily::Road`.
- the generated live autotile atlas has one `road` group rather than distinct road, stone-path, mountain-path, and bridge groups.

These collisions must be removed before path topology can be considered trustworthy.
