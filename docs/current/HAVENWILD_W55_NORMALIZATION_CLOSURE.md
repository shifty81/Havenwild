# Havenwild W55 Building Authority Normalization Closure

Target: `167Z109W55R10C`

W55 does **not** delete the working W46 building pipeline. It separates its responsibilities so there is one owner per concern.

## Locked authority split

| Concern | Canonical owner | R10 disposition |
|---|---|---|
| Logical building identity, room program, semantic transitions, independent interior dimensions | `haven_core::BuildingDefinition` / `BuildingLayout` | **LOCK** |
| Deterministic PCG logical output | `haven_world::BuildingGenerationRequest -> BuildingLayout` | **LOCK** |
| Certified wall/roof/opening/furnishing visual recipe | `haven_assets::BuildingRecipeRegistry` | **KEEP / VISUAL-STRUCTURAL RECIPE** |
| World placement, visual structural instance state, opening/furnishing deltas | `haven_assets::BuildingInstanceRegistry` | **KEEP / PLACEMENT+VISUAL STATE** |
| Cross-reference between logical and visual instances | `BuildingAuthorityBinding` | **BRIDGE ONLY** |
| Dynamic building interior scene identity and dimensions | `BuildingRuntimeSceneRegistry` + canonical `building:<id>:...` scene ids | **LOCK** |
| Entry/exit return authority | `BuildingTravelSession` | **LOCK** |
| Logical building save round-trip | `haven_save::BuildingWorldStateFile` | **LOCK** |
| Editor semantic read model | `haven_editor::inspect_building_layout` | **LOCK** |
| Aggregate acceptance/certification | `haven_tools::certify_w55_building_acceptance` | **LOCK** |

`BuildingRecipe` must no longer be interpreted as the owner of independently sized logical interior scenes. It remains the exact structural/visual recipe consumed by rendering, collision, cutaway, furnishing, and world placement paths. `BuildingLayout` owns semantic topology and may describe an interior scene larger than the exterior representation.

## Fixed-size rule

The project must preserve this distinction:

`world partition dimensions != building exterior footprint != building interior scene dimensions`

`MAP_W` / `MAP_H` remain valid storage-partition constants for the open world. They are not building-interior dimensions.

## Legacy compatibility

- `SceneId::TavernInterior`, `Cellar`, and `GuestFloor` remain compatibility identities only where migration/tests still require them.
- New building archetypes must not add new global interior `SceneId` enum variants.
- Player-facing `Estate` / `Home Estate` remains canonical; internal `farmstead` survives only where old serialized identifiers must remain readable.

## R10 warning disposition

- `runtime_content_mode`: **DELETE STORED FIELD**. The launch mode is consumed during bootstrap/content convergence and did not need permanent `Game` ownership.
- `building_move_allowed()`: **WIRE** into X/Y runtime movement so working BuildingRecipe/BuildingInstance collision authority is actually enforced.
- `canonical_authored_scene()`: **DELETE UNUSED HELPER**. Authored content convergence already loads through the single runtime content authority path.

No warning is silenced with `#[allow(dead_code)]`.

## Certification gate

Before W55 is called locally certified:

1. Root cleanliness audit.
2. Build all.
3. Run tests.
4. Run/inspect consolidated W55 building acceptance certification.
5. Package a fresh complete source rollup and capture a new baseline.

The remote/source-only work may advance to this build point, but local compile/test results remain authoritative before W56 runtime visual changes are trusted.
