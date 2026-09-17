# B04 — Materialized Base World artwork in the Game Canvas

Date: 2026-09-17. Follows the B03 Assets-tab input repair. This is an implementation pass, not a declaration of full-world visual parity or PIE.

## Implemented

- When a selected landmass's visible materialized SceneMap partitions reach at least 3 screen pixels per tile, the World Canvas composes them through the **existing** `scene_render_helpers::draw_scene_tilemap` and `EditorTextureSet` path. This retains source-mapped LPC fill and tuples, existing structural cliff recipe rendering, authored visual overrides, stamps and object textures. No new terrain resolver, texture copy or scene format is introduced.
- Each partition uses a temporary camera whose target is translated by the partition's world-grid origin. Source cells and render recipes remain partition-local while the result is drawn in the same global position as the World Canvas selection, tools and grid. The original camera is restored before selection/authoring overlays.
- Structural bridge results reuse the editor's existing per-scene signature cache, rather than rebaking cliff topology each draw.
- Reuses Scene Canvas composition with `guides: false` to avoid showing every partition's spawn circle, renderable bounds, object bounding boxes and selection artifacts in the continuous view. The normal Scene Canvas remains `guides: true`.
- Low-zoom overview and nonmaterialized/missing SceneMaps stay schematic, explicitly labelled as such. Missing source-backed LPC/user terrain is disclosed on the canvas because the legacy generated base atlas may still be used by the shared Scene Canvas renderer.
- Matches the existing semantic canvas-layer classifications for vegetation, resources, structures, and ordinary props.
- Adds an isolated threshold test for the artwork LOD switch.

## Boundaries / remaining work

- This patch does **not** turn the entire generated geography into finished source-backed tiles. It paints only SceneMap partitions currently materialized and assigned to the selected landmass. Materialization of additional visible partitions, continuous world/landmass coordinate reconciliation, seamless cross-partition asset painting, world-map zoom transitions and editor/client screenshot comparison are separate follow-on work.
- Full-world archipelago overview is still a semantic low-detail map; it must not be sold as runtime artwork. Opening a landmass enters the existing partition-local editor coordinate space.
- The shared renderer may use its existing generated diagnostic atlas/fallback for unavailable source art. Source fidelity depends on the LPC and user-asset texture groups actually loading (the user's previous screenshot reported incomplete texture readiness).
- Play still launches the external development client; **embedded PIE is not implemented**. Do not label a detached window as PIE.
- Linux Cargo/rustc and graphical Windows execution were not available for this source change; only archive, hashes and targeted source invariants can be validated here. The PCC Full Quality Gate and manual comparison are required.

## Windows acceptance checkpoint

1. Apply B03 first if it has not already been applied, then apply B04 through root-drop PCC. Run Full Quality Gate. On compile failure, provide the PCC debug bundle before further changes.
2. Open Base World / Complete World, select and open the central mainland, zoom to at least several pixels per tile. Its materialized partition tile surfaces should now draw atlas-backed artwork rather than flat semantic rectangles. Zoom far out: the overview returns to labelled semantic LOD.
3. Open the same materialized scene in ordinary Scene Canvas and compare one terrain tuple, one cliff, an object or stamp, and an authored override. The world view must not show spurious spawn markers or every object’s diagnostic box. Missing art should be explicitly identified, never declared complete.
4. Move/pan across two **already materialized** adjacent partitions. Confirm source images align with tile coordinates and selection highlighting. Save, reopen, launch external Play, compare the exact same location and report any discrepancies.
5. Exercise Assets ↔ Game Canvas ↔ Pixel navigation, including with the right dock collapsed, to guard against reintroducing B03 input lock.

Follow-on priority: finish actual source texture coverage and contiguous on-demand partition materialization; certify editor/client parity; then extract an embeddable game runtime for in-canvas PIE with reversible Play/Stop.
