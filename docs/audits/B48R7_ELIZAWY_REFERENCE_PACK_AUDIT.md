# B48R7 — ElizaWy source-package cross-audit and guarded waterfall mapping

Scope: `4-season_terrain (1).zip` versus the separately supplied `Terrain.zip`, `FX.zip`, `_ Test Scenes.zip`, and the 2026-09-17 Havenwild source rollup. Reference artwork was NOT altered. This review does NOT certify game runtime, animation timing, collision, editor/client parity, or the B48R6R1 demo scene.

## Identity and provenance

The alternative ZIP includes Eliza Wyatt attribution/credits, distinct `Terrain/Mountain*` and grass/shoreline spritesheets, four animated GIF demonstrations, dedicated `Terrain/Waterfall, Frozen.png`, and `FX/Splash*.png`, `FX/WaterRipple*.png`, and reflection art. Its `Terrain/Credits.txt` calls out original Eliza Wyatt mountain and waterfall artwork and shared LPC contributors for other families. It is an overlapping source presentation, NOT a blind byte-for-byte replacement of the newer aggregated sheets.

- Reference ZIP: 2,630 files (non-directory), 2,621 PNGs, 4 GIFs.
- The alternate `Terrain/Waterfall.png` is 384×608. It matches the **entire left 384×608 pixels** of the original 512×608 `Terrain/Waterfall.png` exactly, yet omits the original's rightmost 128-pixel auxiliary/tiling region. Never replace the 512-pixel atlas with this smaller sheet.
- All six files in `FX.zip` are byte-identical to corresponding `FX/*` files in the reference archive. The seasons demo GIF is also byte-identical across the two sources.
- Frozen waterfall is its own source image (96×224). The separately supplied re-encoded PNG has identical decoded RGBA pixels despite a different PNG file hash. It is not an animation frame from `Waterfall.png`.
- Older source sheets `cliff_summer.png` (512×448) and `terrain_summer.png` (512×832) are composite atlases; the reference ZIP has split seasonal sheets. A matching 32×32 tile may have a **different file and cell address**. Do not substitute sheet names or coordinates without an exact cell mapping.

## 32×32 source pixel audit: reference sheet → main combined atlas

| Summer source family | Exact matching cells | Total cells | Status |
| --- | ---: | ---: | --- |
| Grass | 30 | 30 | Exact tile counterparts located |
| Grass–Shallows | 72 | 72 | Exact tile counterparts located |
| Mountain base | 64 | 70 | Six cells not matched in same combined cliff atlas |
| Mountain animated water | 42 | 42 | Exact tile counterparts located |
| Mountain waterfall transitions | 10 | 42 | **32 tiles not found as exact cells in the same combined cliff atlas**; investigate missing integration, alternate atlas or animated frame conventions |

Winter is NOT layout-identical to summer: the separate winter Grass–Shallows source is 96×384 whereas summer is 192×384; only 2/36 winter grass-shallows tiles match `terrain_winter.png` as exact untransformed cells, and winter mountain animated water is 30/42. The recipe topology can be shared only after per-season source mapping, with winter-ice handled separately. These missing exact matches do not prove the artwork is absent from every other file; they identify a specific atlas-pair discrepancy.

The accompanying `elizawy_summer_atlas_source_crosswalk_b48r7_v0_1.json` explicitly records exact decoded 32×32 pixel matches and **all** candidate target cell locations for summer, including unmatched and ambiguous cells. It does not equate identical artwork with the same gameplay role.

## GIF evidence (actual source; no generated animation)

- `DemoGame - Seasons.gif`: 48 frames, 1024×1184, 80ms per frame. A sample upper-waterfall region cycles through exactly four distinct appearances, repeated three times during its first 12 GIF frames. This visually confirms four animation phases and a **source demo reference tempo of 12.5 frames/s**. Havenwild's current renderer runs its four frames at 7 frames/s. A timing difference is documented; DO NOT change engine timing without review.
- `Cliff Climb Demo.gif`: 24 frames, 768×640. Shows a character climbing vines, an exposed rock face, and a wooden ladder. This is an artistic/traversal reference, not proof Havenwild collisions work.
- `Splash Demo.gif`: 72 frames, 768×768. Illustrates footsteps, ripples, and splash layering around a character in water; the `FX/Credits.txt` describes front/back layering for splashes and ripples.
- `Rotation Demo.gif`: 64 frames, 512×512. Character rotation reference; **NOT a waterfall direction or width specification**.

## Directional water source mapping (review only)

- Four temporal frames occupy 96-pixel-wide strips at x = 0, 96, 192, 288 in the canonical 512-pixel waterfall sheet.
- Each vertical frame contains distinct 96×32 upper row (`y=0`, **north-facing crest candidate**, not full north waterfall certification), demo-matched south visible crest (`y=32`), middle rows (`y=64`, `y=96`) and splash/footer (`y=128`). The parts must remain synchronized by animation frame. A full south frame is 96×160.
- Four west frames are 64×224 at `(frame*96, 160)` and four east frames 64×224 at `(frame*96+32, 384)`.
- The 128-pixel-wide extra strip at x=384 in the canonical atlas remains under review as possible connection/width material. No arbitrary width/stretch/repeat is authorized.
- Current Havenwild runtime draws whole rectangles with north explicitly disabled, while `elizawy_waterfall_connector_catalog_v0_1.json` contains `runtimeEnabled:false` but `runtimeActivation.enabled:true`. This new candidate metadata does NOT silently overwrite either authority or change the renderer.

## Integration contract and blockers

The accompanying `elizawy_waterfall_component_review_b48r7_v0_2.json` gives exact original-source coordinates and component roles; `elizawy_summer_watercourse_review_fixture_b48r7_v0_1.json` describes the target upper river → two drops → recessed pond → southern river topology, but **neither is consumed by the game** yet. The intended scene must prove that pond water reaches the cliff rim, cliff-facing and water-boundary tiles create the correct recessed silhouette, a source-exact crest/shaft/splash connects at both falls, and the corresponding structural levels/collision work in editor and client. Havenwild currently treats standalone one-high cliffs as low-relief details; the proposed 2→1→0 water drops need a clear exception or a legal 2-high arrangement before physical certification.

Next implementation gate: identify source-exact mountain/waterfall-transition cells missing from the aggregated cliff atlas, produce the artist-matched complete summer assembly, and only then connect a shared recipe resolver to both editor and client with collision/animation tests. The existing source rollup is older than the unprovided B22–B48 cumulative **source** patch; do not overwrite its changed files or claim that this add-only package includes those source changes.
