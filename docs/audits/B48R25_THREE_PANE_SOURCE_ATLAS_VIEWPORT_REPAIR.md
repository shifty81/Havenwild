# Havenwild B48R25 — original-source grouping, three-pane mapper and bounded stacked atlas picker

Date: 2026-09-19. **Cumulative PCC candidate; NOT GREEN / not compiled on Windows.** B48R24 is the previous packaged candidate; B48R23 was the last user-verified GREEN when this package was assembled. This ZIP supersedes B48R7 through B48R24 cumulative transports; it is not a complete source rollup. It must be approved and gated as a single transport by project-owned Havenwild PCC.

## Original defects verified in B48R24 source

- A single `draw_source_panel` owns both source-list and current atlas preview; its active sheet is drawn at the same panel origin, and activating additional sheets doesn't draw them in a physically arranged source picker.
- `SourceGroup::from_path` prioritizes filename keywords over the actual original `Objects/Furniture`, `Terrain Objects`, `Structure` and other ElizaWy source folders. Consequently groups can hide genuine original sheets or classify them incorrectly.
- Wheel events change source zoom across much of the left pane; atlas source texture and scene geometry are not clipped to their respective editing viewports, leading to draw-through across panel borders.

## Implemented (existing standalone `apps/haven_atlas_mapper_lite` only)

1. Library rail at 10–15% screen width (14% at standard 1280–1600 widths). Remaining area has equal atlas and scene canvases at startup. Existing divider resizes only atlas/scene at 40–60%; it doesn't take width from the library.
2. ElizaWy original immutable source folder scan only; `Characters` and non-Summer seasonal art excluded from this lane. Filter group memberships use actual original folder topology first (furniture, other objects, structure/buildings, terrain objects, equipment, effects) followed by names for cliffs, water, foliage and base terrain. These are browser classifications, not tile/feature certification.
3. Source list has vertical group controls and a clipped, virtualized independent scroll area. ON/OFF activation remains explicit, and a sheet in use by scene placements cannot be unloaded.
4. Atlas picker draws **all activated source sheets** as distinct, vertically stacked cards in stable path order. One shared pixel scale fits the widest activated sheet initially; cards retain original aspect ratio and correct source identity. A click in any card changes the active source before the drag, preserving correct source ID in placed scene pieces.
5. Mouse wheel over source library scrolls its list. Wheel over atlas picker scrolls the atlas stack; Ctrl+wheel there zooms the picker. Space+drag pans within the atlas content. Wheel over right canvas zooms only the scene. Atlas scroll clamps to content and window resize.
6. Camera viewport clipping confines original atlas art to the middle panel and scene drawing to the scene editing rectangle. GUI chrome is drawn outside the content viewport. Legacy project schema, source IDs, numerical layer values and source hashes are not migrated or rewritten.
7. Retains B48R24 seven-layer controls, undo/redo and approval gates. Source indexing is NOT a mapping approval; no generator button, runtime recipe/collision changes or blanket certification added.

## Validation performed here

- All ten source-level mapper validation scripts pass, including new B48R25 checks of three-pane geometry for 900–2560px window widths and source inventory/provenance; historical tests had their obsolete two-panel assertions replaced with equivalent successor-contract assertions while retaining their other tests.
- The B48R24 predecessor's unchanged ZIP bytes and individual file manifest hashes are checked during packaging. No changes to immutable original source PNGs.
- The patch CRC and all payload SHA256 and sizes are checked after packaging.
- **NOT PERFORMED**: native Rust compilation, Windows PCC gate, GUI mouse/keyboard/scissor behavior, ForgeGUI embedding, client/editor/runtime parity and procedural generation. In particular, camera viewport clipping must be visually checked on the user's GPU and resizable window.

## Windows acceptance test (before calling GREEN or pushing)

1. If B48R24 is already GREEN/pushed, ensure worktree is clean. Drop only the B48R25 cumulative ZIP unextracted at root; run Havenwild PCC intake/approve and Full Quality Gate.
2. Launch mapper through PCC and confirm build label `B48R25 three-column / stacked atlas workspace`, not an old shortcut.
3. Inspect the 10–15% library, then activate **Terrain/terrain_summer.png**, **Terrain/cliff_summer.png**, **Terrain/Waterfall.png**, **Objects/Furniture/Table, Card.png**. Their original categories should appear under Terrain, Cliffs, Water and Furniture respectively. If a source belongs to different expected semantics, retain the source path and report the desired group; do not change certified mappings to fit a browse filter.
4. Confirm four activated sheets are stacked top-to-bottom, fitted to widest and distinct, with no sheet overlap. Scroll picker with wheel; Ctrl+wheel zoom; Space+drag pan horizontally at zoom. Scroll library and scene separately. Clicking/dragging a cell from the *third* sheet must place a scene piece referencing the third sheet, not the previously active sheet.
5. Zoom the middle and right panels aggressively, drag/pan to every edge, resize window and divider. Verify zero art can bleed into adjacent rail, panel chrome, scene or bottom status bar. Confirm layer visibility/lock, Delete, undo, save/open project remain intact.
6. If gate fails, use PCC's auto-generated debug bundle; if GUI fails, capture screenshot, build identifier and exact interaction. Do not push if either fails.

## ForgeGUI hosting dependency

The standalone interface remains Macroquad. A real ForgeGUI migration must **first extract the source index, source selection, atlas layout/clip/gesture and scene document/commands into shared project-owned authoring APIs**, then bind those APIs to a ForgeGUI surface and Havenwild native game canvas. Do not present this source-only GUI pass as ForgeGUI integration or duplicate the terrain resolver/generator inside ForgeGUI. Havenwild PCC remains certification authority until direct Forge delegation has been tested.
