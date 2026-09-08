# Havenwild World-Tile Audit — Both Uploaded Zips

Audited inputs:

- `havenwild-thin-source-20260524-214551.zip`
- `havenwild-clean-source-current-20260524-222502.zip`

Current project direction used for this audit: Havenwild / Havenwild with scene-based interiors, upstairs inn, living tavern operation, farming, fishing, caves, islands, coastal cities, seasons, soil quality, and fishable natural water.

## 1. Zip Structure Findings

### Thin source zip

The thin source zip is smaller and cleaner structurally. It extracts with normal forward-slash directories, includes Rust workspace files, source crates, generated placeholder terrain assets, docs, scripts, and some duplicated nested crate paths.

Key findings:

- Has normal directory layout.
- Contains `assets/generated/prototype_terrain_tiles.json` and `.png`.
- Has duplicated source paths: `crates/tavern_*` and `crates/crates/tavern_*`.
- Includes docs and website assets, including a website `.git` folder that should not ship in a source replacement pack.
- Tile manifest only covers 6 tiles: `grass`, `road`, `water`, `dirt`, `mountain`, `bridge`.

### Clean source zip

The clean source zip contains newer systems and better world-generation work, but the uploaded zip stores many paths with Windows backslashes. On Windows this usually extracts as directories; on Linux it extracts as flat filenames containing `\`. For cross-platform packaging, future zips should use normal forward slashes.

Key findings:

- Has newer world tile enum coverage than the thin zip.
- Adds `SceneBiome`, tile categories, autotile groups, per-tile default interactions, map height storage, and seeded heightmap generation.
- Contains root image artifacts and compiled plugin `bin/` / `obj/` outputs that are not required for a source pack.
- Contains duplicated source paths: `crates/tavern_*` and `crates/crates/tavern_*`.
- Contains legacy content and plugin/mod-kit material that is useful as archive/reference, but not required for the current Havenwild clean source.
- Tile manifest covers 15 tiles but the generated atlas is a single horizontal row while `columns` is set to `5`. That mismatch should be fixed.

## 2. Tile/Worldgen System Comparison

| Area | Thin zip | Clean zip | Audit result |
|---|---:|---:|---|
| Tile size | 32 | 32 | Correct project baseline |
| Map size | 48x32 | 48x32 | Good for prototype scenes |
| Scene model | yes | yes | Correct direction |
| Interior scenes | yes | yes | Supports black-void/scene-interior direction |
| Biome enum | no | yes | Clean zip is newer |
| Height storage | no | yes | Clean zip is newer and needed |
| Water depth tiles | basic water only | water/shallow/deep | Clean zip is better |
| Coast tiles | none | sand/wet sand/pebbles | Clean zip is better |
| Mountain/cliff tiles | mountain placeholder | cliff/mountain rock/path | Clean zip is better |
| Cave tiles | cave floor/wall | cave floor/wall | Both have basics |
| Farm tiles | dirt/tilled/crop/greenhouse | dirt/tilled/crop/greenhouse | Still needs soil quality states |
| Autotile metadata | partial | partial | Needs formal metadata and resolver |
| Atlas manifest quality | very basic | better but mismatched columns | Needs replacement |
| Seasons | not represented | not represented | Missing for current specs |
| Fishable water metadata | not represented | water tiles exist but no fishable metadata | Missing for current specs |
| River/coast flow rules | not represented | partial heightmap logic | Needs exact spec |

## 3. Current Source Worldgen Strengths

The clean zip is the better base. It already has:

- 32x32 tile standard.
- Scene IDs for farmstead, tavern interior, cellar, guest floor, roads, fields, woods, cave mouth, and cave depths.
- Scene kinds: exterior, interior, cave.
- Scene biome concept: temperate, coastal, highlands, cave.
- Tile categories: terrain, floor, wall, farm, water, special.
- Autotile groups for road, floors, water, walls, cliffs, cave walls.
- Height data saved alongside tile rows.
- Height-based generator controls for water level and mountain level.
- Height classification that can produce water depth, shore bands, cliffs, mountain rock, sand, dirt, grass, and tall grass.
- Runtime tile detail drawing that makes flat rectangles more readable.

## 4. Critical Gaps Against Havenwild Requirements

### A. Tile definitions are still too hardcoded

The code enum is useful for prototyping, but real worldgen needs data-driven tile metadata. Tile data should live in JSON/RON/TOML and include:

- walkable
- buildable
- fertile
- fishable
- liquid
- blocks building
- interior only
- autotile group
- height band
- biome tags
- season tags
- variant count
- interaction defaults

### B. Tile states should not all become unique tile enums

The current project needs soil quality, watered soil, fertilized soil, crop stages, seasonal tinting, construction zones, cleanliness, and room zones. These should mostly be state layers, not one hardcoded enum value per condition.

Recommended separation:

- Base tile: grass, dirt, water, floor, wall, cliff.
- State layer: wet, fertilized, crop stage, snow, construction, dirty, room zone.
- Overlay/stamp layer: flowers, pebbles, reeds, leaves, path wear, puddles.

### C. Water needs to become fishable world data

The game direction says all natural water should be fishable. Current `Water`, `ShallowWater`, and `DeepWater` are only tile kinds/interactions. They need metadata for:

- fish habitat
- fish population table
- river/coast/lake/sea flags
- depth class
- current/flow direction
- seasonal availability
- boat-safe depth

### D. Shoreline generation needs exact bands

The current clean height classification is directionally right, but it should become an explicit pipeline:

1. height field
2. deep water
3. water
4. shallow water
5. wet sand / mud / pebble shore
6. sand / grass / dirt based on biome
7. land vegetation
8. cliffs/mountains

### E. Autotile resolver is not complete yet

The code draws borders/bevels based on neighbors, which is helpful, but it does not yet resolve a full tile-variant atlas by mask.

Needed:

- 8-neighbor mask calculation.
- Per-group mask-to-variant mapping.
- Edge/corner transition families for water, shore, roads, cliffs, cave walls, floors.
- 3x3 preview in editor.
- Validation when a tileset lacks required variants.

### F. Seasons are missing from the tile art/spec

The direction says seasons matter as a core pillar. Tile metadata should prepare for seasonal variants:

- spring/summer/autumn/winter grass
- snow overlays
- frozen/iced water later
- seasonal flowers/leaves
- crop calendars
- wet/muddy rain states

### G. Atlas format mismatch

The clean zip manifest says `columns: 5` but the generated `prototype_terrain_tiles.png` is one row of 15 tiles. This makes index-based atlas lookup ambiguous.

Replacement provided in this pack:

- `assets/generated/prototype_terrain_tiles.png`: 25 tiles in a true 5x5 grid.
- `assets/generated/prototype_terrain_tiles.json`: updated manifest with exact atlas coordinates.

## 5. Recommended Near-Term Replacement Strategy

Use a two-tier tilesheet approach:

### Tier 1: code-compatible replacement

Use `assets/generated/prototype_terrain_tiles.png/json` from this pack.

It matches the clean source `TileKind::ALL` order exactly:

1. grass
2. tall_grass
3. sand
4. wet_sand
5. pebble_shore
6. road
7. stone_path
8. mountain_path
9. wood_floor
10. plank_floor
11. stone_floor
12. brick_floor
13. wall
14. cliff
15. mountain_rock
16. dirt
17. bridge
18. cave_floor
19. cave_wall
20. tilled_soil
21. crop
22. greenhouse_zone
23. water
24. shallow_water
25. deep_water

### Tier 2: expanded future worldgen atlas

Use `assets/generated/havenwild_world_tiles_expanded_v1.png/json` as the next target once the source moves from enum-only tile kinds to data-driven tile definitions.

It includes 48 terrain/farm/water/coast/interior/cave tiles for:

- temperate grass variants
- seasonal grass variants
- soil states
- coastal shorelines
- water depth and flow
- roads and paths
- tavern/interior floors
- caves and ore floor
- dark interior void support
- greenhouse/farm states

## 6. Implementation Order

1. Replace the current generated terrain PNG/JSON with the code-compatible replacement.
2. Add `content/worldgen/biome_presets.json`.
3. Add `content/worldgen/tile_transition_rules.json`.
4. Wire metadata loading into `haven_core` without removing current enums yet.
5. Add an editor palette that reads metadata categories instead of raw enum order only.
6. Add worldgen validation:
   - all tiles referenced by biome presets exist
   - all required height bands have a tile
   - every liquid tile has fishable/depth metadata
   - every autotile group has at least placeholder variants
7. Add seasonal/state overlay layers instead of expanding `TileKind` for every state.
8. Add fish population data to water tiles.

## 7. Clean Source Recommendation

For the next clean source zip, keep:

- `Cargo.toml`, `Cargo.lock`, `tools/build/Build.ps1`
- `crates/haven_core`, `crates/haven_editor`, `crates/haven_game`
- `assets/generated` only for generated source-friendly placeholder assets
- `content/worldgen`
- `content/packs`
- `docs/design`, `docs/engineering`, essential `docs/sdk`
- `SCRIPTS`

Move out/archive:

- root loose screenshot/image artifacts
- nested `crates/crates/*` duplicate source
- `docs/website/.git`
- compiled plugin `bin/` and `obj/` outputs
- old Travellers Rest mod plugin binaries unless specifically needed
- legacy experiments into an archive zip

## 8. Bottom Line

The clean zip is the correct base, but it still needs a world-tile metadata layer before this project can support the required Havenwild gameplay: seasons, fishable water, soil quality, coastlines, islands, caves, interiors, room expansion, and long-term procedural scene generation.

This replacement pack gives the project a stronger immediate tilesheet and the exact metadata direction needed for the next implementation pass.
