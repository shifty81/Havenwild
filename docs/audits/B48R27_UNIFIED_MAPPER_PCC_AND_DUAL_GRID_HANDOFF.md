# Havenwild B48R27 — PCC bridge and dual-grid convergence

**Baseline:** `experimental` B48R25 commit `796895a5dd2aae3cbf3dcca37f73a54df94969ad` plus the previous B48R26 cumulative member included in this ZIP. Never apply the September 17 rollup over the B48R25 source. **This patch is cumulative B48R26–B48R27 only, not cumulative from B48R7 or a complete source rollup.** No existing source files are overwritten or removed.

## Completed here (backend foundation, not full GUI)

- Preserves every B48R26 source recovery file, documentation and reference evidence byte-for-byte.
- Adds `apps/haven_atlas_mapper_lite/tools/pcc_bridge.py` which discovers the *live* PCC command registry through the existing `tools/forge/HavenwildPccProvider.py`, retrieves capabilities/status, returns command plans, and optionally delegates an exact confirmed registered command to the canonical project PCC. No PCC operation scripts were copied into the mapper and no second patch ledger exists. A non-read-only command additionally requires `--allow-mutation`. Execution is synchronous in this CLI **only**; a future GUI must spawn it in a non-blocking external process and follow PCC receipts.
- Adds a diagnostic-only `dual-grid-report` that inventories the existing 34-family tuple catalog and named half-tile anchor, and reports the stale +1 elevation policy from the older authority document. It does not map legacy tuple IDs to original ElizaWy sprites, certify art, or replace the runtime resolver.
- Adds a machine-readable migration contract and tests.

## Example commands (Havenwild root)

```
py -3 apps\haven_atlas_mapper_lite\tools\pcc_bridge.py capabilities --root .
py -3 apps\haven_atlas_mapper_lite\tools\pcc_bridge.py commands --root .
py -3 apps\haven_atlas_mapper_lite\tools\pcc_bridge.py status --root .
py -3 apps\haven_atlas_mapper_lite\tools\pcc_bridge.py dual-grid-report --root .
py -3 apps\haven_atlas_mapper_lite\tools\pcc_bridge.py plan --root . --key audit.terrain-tuples
```

No command is executed by `plan`. For actual execution, the GUI should present the exact key, current project, lane, unsaved-state check and user confirmation, then spawn `run --root . --key KEY --confirm-key KEY --allow-mutation` as a separate process. Do not send arbitrary shell strings or bypass the provider. Interactive menu actions that require TTY should keep their existing PCC front door rather than pretending a subprocess call is a full GUI migration. Root-drop patches still enter the canonical PCC intake; a tool must never directly manipulate `.havenwild/pcc/patch-ledger.json` or mark its own gate GREEN.

## Why the existing tuple system needs convergence, not replacement

`content/terrain/havenwild_terrain_tuple_catalog_v1.json` already declares 34 material ordinals, 15,562 distinct four-part signatures, 15,653 tuple mappings and 31 duplicate signatures. `crates/haven_spatial/src/lib.rs` defines `TerrainTuplePresentationOrigin`. `content/worldgen/terrain_v2_wang_resolver_contract_v1.json` describes source-exact lookup with an unresolved-result policy. These prove groundwork exists; none prove the catalog is an approved coordinate lookup for the original ElizaWy summer atlas. Do **not** auto-mark the whole tuple catalog approved or regenerate 15,562 synthetic ElizaWy tiles.

For **source-supported** ground transitions, authored semantic owner cells feed the shared resolver. A display tile sees four owner-cell material corners and uses the established corner-signature format to select a verified source recipe. For a binary grass/dirt transition there are at most 16 corner combinations; only the variants actually supported by source art can be published. More than two materials require a verified compatibility policy or explicitly authored combination. A missed recipe returns an unresolved diagnostic, not a nearest-looking sprite. Existing Wang/8-neighbor resolver paths may remain when the source topology actually calls for them; dual-grid does not override them.

The terrain's draw cell is a **layered assembly**, sometimes informally called a tuple: ground surface + cliff/rim/body + rock/water contact + hydrology/water + waterfall/FX + foreground can occupy related grid positions with explicit source references and draw order. It is not correct to use the same visual sprite as collision or water simulation. Structural elevation is real `0..30` including +1. Before runtime publication, remove retired `Level 1 is reserved` and `0/2/3/4` policies from executable validators, runtime and worldgen and migrate persisted values deliberately. Water contact and waterfall direction require source-exact authored geometries, not 16-way dual-grid masks.

## User-facing unified workbench target (not completed)

Left: immutable source categories, nested source family, season, active sheets. Middle: scrollable multi-atlas picker + **large editable Summer Master** scene. Right: two modes, **Brushes** (approved ground/water/transition/structural-feature tools) and **Inspector** (selected composite, source crops, collision, adjacency, elevation, sockets, seasonal overrides). Bottom: persistent project console, PCC job progress/logs, patch intake and gate receipts. One toolbar provides Generate, Save, Validate, Review, Stage candidate; its buttons invoke shared commands. Do not call Stage Missing a procedural generator. Do not place the rejected B48R10 scene.

The B48R26 artist-demo recovery provides 485 unique source matches, 242 ambiguous placements and 457 unmatched/layered cells across 1,184 cells. Preserve ambiguity. The approved earlier waterfall composition is a separate review input. Next pass must construct/edit the source-authored pond/cliff/river scene, then connect one actual shared seeded worldgen resolver to the mapper and editor/client. A correction is saved as scene-specific until user explicitly promotes a reusable recipe; require adjacency and collision validation and visual approval before publication. Rerolls should report missing combinations, not silently learn incorrect art.

## Tests and limitations

Run `py -3 -m unittest discover -s apps\haven_atlas_mapper_lite\tests -p "test_b48r27*.py" -v` and rerun B48R26 tests. This environment only verifies Python, JSON, archive checksums and an isolated fake PCC provider; it does **not** build the Rust application, integrate new panels into the GUI, run the Windows full gate, or publish recipes. The B48R25 GUI source remains untouched. Full native GUI/PCC migration is not claimed.
