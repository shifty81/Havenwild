# Havenwild H11–H20 Geography / Streaming Checkpoint

## Purpose

This handoff deliberately freezes the project at **H20** so the editor/worldgen/streaming foundation can be compiled and debugged before the later farming, unified TAB/Journal, metadata-repair, proof-map, and H30 presentation work is layered on top.

Baseline rollup: `Pass167Z109W81R30R44H7`  
Baseline SHA-256: `6d32f479de7f82645210700ea14adfa4a235217b94f35ed840e8355d7ac79e4c`

## Included closure

- **H11** — Bottom Validation dock: complete rows, scrolling, Top, Copy All, persisted scroll position.
- **H12** — Runtime-ready published assets injected as individual Asset Browser cards with real thumbnails.
- **H13** — Browser selection retains the exact published placeable ID and routes through the existing semantic placement authority.
- **H14** — Existing exact placeable preview/placement authority retained and certified; published cards now feed it correctly.
- **H15** — Existing assembled Character Studio preview authority retained and certified.
- **H16** — World-preview far LOD normalized from 12 to power-of-two step 16.
- **H17** — Elevation macro-features use deterministic bent ridge bands rather than ellipse plateaus; emergency fallback uses the same ridge grammar.
- **H18** — Freshwater riparian shoulders no longer expose a hard MountainRock curb; continuous waterfall edges have one animated sprite owner. Existing harbor landfall/reservation authority remains intact.
- **H19** — Generated ramp corridors cannot cross freshwater.
- **H20** — Background prepare/persistence/hydrology/structural workers, bounded publication, stale hydrology rejection, local structural solves, asynchronous exploration persistence, fail-closed chunk crossing, and development streaming telemetry.

## Explicitly NOT included

These already-started items are intentionally held for the next checkpoint so this build isolates H11–H20:

- farm wet-soil/seed/crop progression and freshwater retention;
- world-metadata repair UI/runtime;
- generated-world proof-map toggle;
- Scene Chunk Pixel Studio reframing;
- unified Character/Inventory/Crafting/Journal/Map TAB shell;
- enlarged in-game live paper doll;
- title-screen-theme in-game GUI normalization;
- H30 ElizaWy/ramp post-composition changes.

## Static certification

- Focused H11–H20 closure audit: **24/24 PASS**.
- Existing content-integrity suite: **18/18 PASS**.
- JSON parse audit: **PASS**.
- Modified-Rust conflict/delimiter lexical audit: **PASS**.
- Rust compile/test: **UNVERIFIED HERE** — sandbox has no `cargo`/`rustc`.
- Architecture validator: inherited-red on the pristine baseline due existing oversized modules; not treated as a new H11–H20 compile failure.

## Windows build gate

Apply this ZIP through the normal Havenwild root-drop/update-inbox flow, then run **Full Quality Gate**. If the gate is green, launch both editor and client.

### Editor acceptance

1. Open Bottom Dock → Validation. Verify mouse-wheel/PageUp/PageDown scrolling, **Top**, and **Copy All**.
2. Open Asset Browser. Verify published trees/props/components appear as individual entries rather than only whole sheets.
3. Select a published entry and place it in Scene/World authoring. Verify the exact selected visual/ID is used.
4. Inspect Character Studio assembled preview.
5. Zoom the complete World Editor view far out/in and verify geography no longer morphs at a non-power-of-two far LOD.

### Client/worldgen acceptance

1. Generate/start a development world from a fresh seed where practical.
2. Inspect elevated geography: look specifically for elongated/bent ridges rather than repeated circular mesas.
3. Follow rivers along elevated areas. Banks should use a natural dirt/grass shoulder instead of a continuous rock curb.
4. Inspect waterfalls, especially wide rivers. A continuous fall edge must not stack multiple giant waterfall sprites.
5. Inspect ramps around rivers: generated ramps must not run through freshwater.
6. Walk continuously into several unexplored/new chunk boundaries while holding movement. Movement should no longer pause to synchronously generate/load/save terrain.
7. With development telemetry visible, watch prepare/persist/hydrology/structural backlog and `frame ... ms` while crossing boundaries.
8. Save, exit, reload, and cross previously visited/new boundaries again to exercise cached and uncached paths.

## Debug feedback requested

If anything fails, return the Full Quality Gate/debug bundle plus screenshots of:

- first compile/runtime error;
- representative ridge/cliff/river/waterfall/ramp area;
- streaming telemetry during any hitch;
- Asset Browser/placement issue if an exact published asset does not survive selection.
