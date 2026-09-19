# B48R9 — ElizaWy mapping: verified source coverage and remaining work

## Evidence and scope

- Inputs: user-supplied `4-season_terrain (1).zip`, `Terrain.zip`, B48R7 and B48R8 PCC patches, plus the September 17 full source rollup for existing contract inspection.
- This pass verifies **source address/pixel identity only**. It does not classify every tile into a final visual role or alter renderer, editor, collisions, elevation, world generation, or full PCC certification.
- Previous B48R8 GREEN was reported by the user; B48R9 is a new additive patch and has **not** passed the Windows full PCC gate.
- Source archive contains 40 PNG terrain sheets and 1,781 source cells of 32×32 pixels (one source cell record per split sheet). Multi-season reuse yields additional per-season target crosswalk observations. 290 pre-existing B48R7 summer entries and all 42 B48R8 summer transition source hashes were reconciled exactly.
- Truncated large sets of global fallback coordinates are identified by `globalMatchesTruncated` with `globalExactMatchCount`; these fallback matches are evidence, **not** runtime-selected slots. Transparent all-zero tiles produce ubiquitous ambiguous matches and must never be auto-selected.

## NEW: Important winter mapping correction

- The separately supplied winter `Grass-Shallows` sheet maps **all 36/36 exact cells** to `terrain_winter_ice.png`, but only 2/36 to `terrain_winter.png`. The same is true of winter `Dirt-Shallows` (36/36 versus 2/36). Thus the former 34/36 apparent gaps are a **wrong target-atlas comparison**, not missing source pixels.
- Keep winter and winter-ice as separate profiles. This cross-profile exact match is a *candidate source routing finding*, not permission to switch winter gameplay or visuals automatically.

## Seasonal cliff-water source crosswalk

Family | Spring source matched canonical | Summer | Autumn | Winter | Status
---|---:|---:|---:|---:|---
Mountain base | 64/70 | 64/70 | 63/70 | 64/70 | Source-coordinate identity only
Mountain features | 26/28 | 26/28 | 26/28 | 26/28 | Source-coordinate identity only
Mountain vines | 27/30 | 27/30 | 30/30 | 30/30 | Source-coordinate identity only
Mountain animated water | 42/42 | 42/42 | 42/42 | 30/42 | Source-coordinate identity only
Waterfall transitions | 10/42 | 10/42 | 10/42 | 10/42 | Source-coordinate identity only
Grass-shallows | 72/72 | 72/72 | 72/72 | 2/36 | Source-coordinate identity only
Dirt-shallows | 72/72 | 72/72 | 72/72 | 2/36 | Source-coordinate identity only

## What remains to MAP, in implementation order

### A. Cliff-water interfaces: B48R9 continuation (highest priority)
- Classify and visually assemble the **42 cells per season** of the source-authored mountain/waterfall-transition sheet into exact top-bank lip, left/right shoulder, cliff-facing pond wall, submerged rock-to-water edge, inlet/outlet, and lower impact roles. The four seasons each have **32 exact cells absent from the older combined cliff atlas**; summer sheet was recovered in B48R8, spring/autumn/winter currently require governed separate source hydration or exact asset-pack mounts.
- River/waterfall edge contacts must butt together without blue rectangles, abrupt vertical water cuts or exposed grass gaps; prove source-cropped seams using original artist summer demo. Classify both width variants independently; no arbitrary cropping/resampling.
- Fix the approved-looking waterfall *context*, not the falling-water sprite itself; the latest diagnostic does not prove the pond recess or waterfall contacts.
### B. Discrete elevation and cliff terminals
- Map full left/right taper terminal sets, north-facing termination, inner/outer corners, straight continuity, passage openings and water-facing terminators. Prior cliff grammar maps 224 source-address cells and 15 structural masks, but visual acceptance of all assemblies/runtime projection remains incomplete.
- Author the recessed pond with visible one-tile face as a **basin/low-relief exception**, not a silent rewrite of the established minimum two-level TRUE cliff rule. Prove 2->1->0 water flow separately from walkable cliff traversal policy.
- Verify ordinary narrow cave source 1×3 and reserved wide 3×3 entrance, ladders/vines and collision connector ownership, including all cliff directions and terminal details.
### C. Complete terrain families and seasons
- Resolve unaddressed source-only mountain-base/feature/vine and winter animated-water cells. Do not infer that a cell missing from the combined atlas is absent from the split source pack.
- Promote actual topological grass/dirt/sand, shoreline, shallow/deep water, corner, concave/convex coast and pond recipes; eliminate B48R8 demo hard water/grass edges.
- Map winter-ice shoreline and frozen waterfall separately; audit the frozen 96×224 source image and four-season frame/FX contracts without auto-animating frozen art.
- Validate season-specific source coordinates, even for source-geometry-compatible cliff sheets; preserve B43 winter review approval *only* for the board previously accepted.
### D. Everything after structural terrain
- Vegetation: per-season trees/shrubs/flowers/crops/forage, connected sprites, footprints, canopy overlap, collision and harvest states.
- Structures: modular fences, bridges, doors, roof/wall/floor sets, stairs, cave portals and opening direction variants.
- Objects: furniture, small items, wall items, moving/interactable props, anchors and collision/occlusion.
- Effects: water splash back/front, ripples, reflections, environmental and animation frame timing.
- Characters: broad 63,973-PNG source inventory exists in `Characters.zip`; need compatible body/clothing/hair/props composition, animation/collision/registration in manageable families rather than one global blanket approval.

## Existing project contracts — avoid reinvention

- Full Sept17 source includes `content/worldgen/elizawy_cliff_complete_mapping_v0_1.json`, `elizawy_cliff_sheet_role_catalog_v0_1.json`, `elizawy_cliff_source_grammar_authority_v0_1.json`, `cliff_cave_mouth_policy_v0_1.json`, and runtime structural cliff/waterfall Rust implementations.
- Review existing 15-mask cliff shape mappings and supersession notes before creating any new visual variants. Existing catalog has a `runtimeEnabled`/nested `runtimeActivation.enabled` discrepancy; B48R7 metadata explicitly does not enable north.
- Existing renderer uses full waterfall rectangles, not B48R7 component mapping, and the B48R7 watercourse JSON is still a reference-only fixture.

## Evidence requirements before promoting into the game

1. Exact cells and source-hashes -> 2. assembly edge and corner proof -> 3. source-exact combined summer scene -> 4. shared renderer/editor recipe -> 5. structural collision/elevation/flow tests -> 6. season-specific proof -> 7. Windows PCC full GREEN.
No new art or AI-generated assets; no unverified north activation; no blanket adoption of source-identical but semantically ambiguous cells.

## Validation provided

`python tools/automation/validation/checks/assets/Validate-ElizaWySeasonalCrosswalkB48R9.py` checks integrity and schema. Supply original archive ZIPs via its flags to verify every source pixel and exact mapped canonical coordinate. Use the optional B48R7/B48R8 ZIP flags to confirm inheritance.

## Patch behavior

Additive only, new paths; **not** a complete cumulative source rollup. Requires current B48R8 GREEN checkout. No application/runtime files touched, and no generated global ZIP should be dropped into the repo root as an update.
