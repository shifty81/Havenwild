# Havenwild Terrain Completion Matrix

Date: 2026-07-15

This matrix defines what “terrain complete” means before the project expands to
bulk LPC biome/season/interior ingestion.

Status meanings:

- `production`: safe default behavior.
- `preview`: usable but still needs topology, pair, or editor polish.
- `incomplete`: known missing behavior that must be fixed before calling the terrain family complete.
- `deferred`: intentionally outside the current overworld terrain pass.

Paint modes:

- `direct`: normal editor brush.
- `advanced`: visible only with an advanced/generated badge or advanced filter.
- `generated`: produced by worldgen, normalization, gameplay, or shore/depth rules.
- `deferred`: reserved for later scene/object/gameplay systems.

| Tile | Group | Paint | Status | Main remaining work |
| --- | --- | --- | --- | --- |
| grass | Ground | direct | production | Detail/rare-detail sliders and seasonal variants. |
| tall_grass | Ground | advanced | preview | Decide whether it is a terrain variant or vegetation overlay. |
| dirt | Ground | direct | production | Detail/rare-detail sliders and seasonal variants. |
| sand | Ground | direct | production | Shore normalization and seasonal/biome variants. |
| wet_sand | Shore | generated | incomplete | Auto-generate from sand touching cardinal water; render through canonical terrain-v7 Sand source; normalize inland wet sand back to sand. |
| pebble_shore | Shore | advanced | incomplete | Split from stone path; add sand/dirt/water pair rules. |
| shore_foam | Shore | generated | incomplete | Generate only on valid shore/water edges. |
| mud_bank | Shore | advanced | preview | Wetland/cave mud pair coverage and spawn rules. |
| road | Paths | direct | production | Pair coverage against ground/shore and optional overlay mode. |
| stone_path | Paths | direct | incomplete | Split from pebble shore; add sand/dirt/grass pair coverage. |
| mountain_path | Paths | direct | incomplete | Add sand/dirt/grass pair coverage. |
| bridge | Paths | advanced | preview | Convert to structural/stamp placement over water. |
| water | Water | direct | preview | Pure fills may animate through authored water variants; mixed coast/depth geometry must stay stable. |
| shallow_water | Water | direct | preview | Enforce as land/deep-water border; render through terrain-v7 Water so shallow/deep uses authored depth transitions. |
| deep_water | Water | direct | preview | Prevent direct 8-neighbor shore contact with a shallow-water buffer; clean square patch artifacts. |
| river_water | Water | generated | incomplete | Generate as river channel material. |
| river_mouth_blend | Water | generated | incomplete | Generate where river meets ocean/lake/shore. |
| ocean_shallow | Water | generated | incomplete | Generate as coastal ocean band using terrain-v7 Water; shore foam handles beach-adjacent visual wetness. |
| ocean_deep | Water | generated | incomplete | Generate as open-ocean interior. |
| cliff | Rock | direct | incomplete | Dedicated structural cliff topology and transitions. |
| mountain_rock | Rock | direct | incomplete | Dedicated rock/cap topology and transitions. |
| cave_floor | Cave | direct | preview | Cave-specific variants and pair coverage. |
| cave_wall | Cave | direct | incomplete | Same-family cave wall assembly and cave topology. |
| wall | Interior | direct | preview | Interior wall groups and room/building assembly. |
| wood_floor | Interior | direct | preview | Interior grouping and thumbnails. |
| plank_floor | Interior | direct | preview | Interior grouping and thumbnails. |
| stone_floor | Interior | direct | preview | Interior/cave grouping and thumbnails. |
| brick_floor | Interior | direct | preview | Interior/town grouping and thumbnails. |
| tilled_soil | Farm | direct | production | Farm lifecycle integration. |
| watered_soil | Farm | direct | production | Farm lifecycle integration. |
| crop_seedling | Farm | generated | incomplete | Gameplay crop state, not normal terrain painting. |
| greenhouse_zone | Deferred | deferred | deferred | Greenhouse stamp should transition to greenhouse interior scene. |

## Immediate pass order

1. `Pass120`: lock terrain/biome/asset registries and validate the contract.
2. `Pass121`: shore/water normalization.
3. `Pass122`: canonical terrain-v7 source-family normalization for all currently mapped terrain.
4. `Pass123`: path/ground pair coverage.
5. `Pass124`: structural cliff/mountain-rock topology.
6. `Pass125`: editor terrain browser with thumbnails, badges, search, biome/season selectors, and detail sliders.
7. `Pass126`: seasonal terrain atlas reuse from compatible LPC sheets.
