# B48R26 — Artist-demo source recovery, not a finished mapper

**Baseline:** experimental B48R25, GitHub commit `796895a5dd2aae3cbf3dcca37f73a54df94969ad` (verified 2026-09-19). The September 17 rollups are earlier than this checkpoint: DO NOT overwrite B48R25 source using them.

**This patch is a bounded additive recovery helper only.** It does not replace `apps/haven_atlas_mapper_lite/src/main.rs`, touch the PCC, modify original image assets, publish mapping, claim GUI improvements, or certify a live scene. Preserve all existing B48R25 source, earlier visual approvals, and installed originals. No Windows Full Quality Gate was run here. The rejected B48R10 scene stays rejected.

## What it actually provides

`apps/haven_atlas_mapper_lite/tools/recover_eligible_summer_demo.py` compares artist-provided `4-season_terrain (1).zip` against the original `_ Test Scenes.zip` summer demo using complete 32x32 RGBA tile equality. Installed source PNGs are accepted **only** if their bytes match the original pack's members. For every reference-grid cell it records all exact matching source addresses. **Only uniquely matching cells** become editable, unreviewed `havenwild.atlas_mapper_project.v0_7` pieces. Ambiguous sources are not arbitrarily selected; layered, animated, shifted, or otherwise unmatched areas remain unplaced. It emits a per-cell report and diagnostic overlay of the original artwork. No independent artwork is generated.

### Actual recovered reference data (supplied archives)

Artist summer demo: 1024x1184, 32x37=1184 aligned cells. Eligible pack: 29 Summer/neutral sheets; 28 were complete 32px grids. `Terrain Objects/Flowers - Wildflowers (Summer).png` is non-grid-sized and deliberately excluded from this *tile-only* algorithm, not from the full asset lane. Source identity is byte-verified, and seven distinct source sheets contribute uniquely matching tiles. Of 1184 demo positions: **485 uniquely matched**, **242 ambiguous but exactly matched**, **457 unmatched/layered**. These values are reference coverage, **not** semantic mapping or gameplay approval. There are no inferred heights, collision profiles, water levels, cave behavior or procedural placement recipes.

### Reproduce without overwriting the summer master

Extract the original `4-season_terrain (1).zip` using the project's governed source-library intake so its `Terrain/` and `Terrain Objects/` directories are together under one immutable original-pack directory. Do NOT extract into or modify pre-existing source folders without provenance checks. From Havenwild root, with Pillow already available:

```powershell
py -3 apps\haven_atlas_mapper_lite\tools\recover_eligible_summer_demo.py `
  --repo . `
  --source-root "assets\source\licensed\lpc_revised\YOUR_ORIGINAL_4_SEASON_PACK" `
  --pack-zip "PATH\TO\4-season_terrain (1).zip" `
  --demo-zip "PATH\TO\_ Test Scenes.zip" `
  --out "artifacts\asset-intake\atlas-mapper\projects\elizawy_summer_reference_recovery_candidate.mapper.json"
```

Specify the **actual** installed pack directory, not a guessed one. The recovery tool never installs assets or overwrites a project. If an installed original differs from the ZIP it is excluded, reported, and never silently replaced. Open the candidate with **Load Project** only after the tool reports verified source paths. It is a starting point for recovering actual artwork positions, **not** the visually approved complete summer master; do not rename it to the master file or use it for procedural generation.

Run the isolated tests:

```powershell
py -3 -m unittest discover -s apps\haven_atlas_mapper_lite\tests -p "test_b48r26*.py" -v
```

The earlier B48R25 GUI and PCC source need their own Windows build, interactive smoke and Full Quality Gate. This patch's source tests passing are not equivalent.

## Research conclusion: keep three distinct mappings, one underlying authority

1. **Source inventory:** immutable original sheet/path/hash + 32px source crop or correctly sized multi-cell rectangle. Categorize `Terrain/Ground`, `Terrain/Transitions`, `Cliffs/Elevation`, `Water/Contact`, `Waterfalls`, `Traversal/Portals`, `Vegetation`, `Structures`, `Props`, and `FX`. A source folder/sheet category is NOT its placement role; mixed sheets may expose several roles. Characters stay a separate tool lane.
2. **Semantic assembly:** material surfaces; source-exact Wang/dual-grid corner roles where appropriate; elevation-dependent cliff crest/body/foot/terminals; water-to-rock transitions; compound features (waterfall, cave, vine, ladder, bridge). Each assembly needs exact source crop, authored structure and adjacency/connectivity, compatible seasonal variants, and layer/subcell drawing order.
3. **Runtime behavior:** canonical terrain elevations 0..30, including legitimate +1 cliffs, water surface/elevation and depth, per-cell/feature collision and traversability, animation, scene transitions, editor/client/worldgen shared recipe publication. These must come from one shared authority and be tested; a painting UI must not invent a second rule set.

### Where dual-grid belongs

Apply dual-grid only to surfaces and transitions whose **actual source artwork and verified atlas topology** support 4-corner material combinations. It selects visual variants from neighboring material corners; it is **not** a universal substitute for cliff orientation/height, layered water contacts, modular waterfall mouths or cave traversal. These still require directional structural recipes and composition. Existing Havenwild terrain/water semantic separation should be audited at the shared resolver and persistence boundaries, *not* removed blindly. A draw-layer composite/tuple can contain ground, cliff face, water contact, animated water, splash, and foreground overlays at the same logical cell, each retaining source references, z-order, elevation and distinct gameplay semantics. "Tuple" is a composition/record concept here, not a specific required Rust type.

### Collision authoring acceptance

A candidate collision/traversal editor needs tile footprint, impassable cliff-face mask, true walkable upper/lower surfaces, water/swim policy, directional connector graph and portal threshold, all independently visualizable. Waterfalls cannot be walked through simply because the water art appears continuous. A cave is a multi-cell feature; wall art is solid except an explicitly authored threshold and destination. Cliff terminal openings are traversable **only if walkable ground and navigation genuinely connect at the elevation boundary**. Source-authored ladder, vines and indentations supply actual routes; coastal one-level water-facing cliff access uses water-appropriate routes rather than arbitrary ladders. Do not restore the retired minimum-two-level cliff restriction or level-1 promotion.

## Next bounded functional implementation (not delivered here)

**B48R27** should refactor B48R25's `main.rs` into shared project/atlas/scene commands while retaining the existing app and schema; add an independent *right-side* mapped-surface palette to paint already approved terrain brushes without covering the canvas. Use categorical asset indexes with multi-atlas activation and distinguish file categories from per-crop roles. Load the candidate recovery scene and the approved B48R9 waterfall as reference-only sources. Implement a **complete, authored, editable summer demonstration** with source-exact waterfall lips/feet, recessed pond walls/corners, submerged cliff contacts, +1 terrain elevation and source-backed climbing/caves. Only then connect a seeded shared resolver and reroll -> edit -> candidate recipe -> topology/visual/collision tests -> approval -> Asset Authority publication. Full GUI migration to ForgeGUI is a separate gated dependency; do not rebuild the mapper from scratch or falsely relabel Stage Missing as generation.

**Status:** source-proof candidate + validation utility delivered; no GUI change, no certified full scene, no generator, no PCC GREEN.
