# B03 — Assets navigation hotfix and Base World rendering acceptance

Date: 2026-09-17. Applies **after** B01E02+B02 GREEN. This is a narrow corrective patch, not a new PCC or renderer.

## Confirmed root causes

1. `apps/haven_editor_native/src/app/input.rs` treated an open Assets workspace as if canvas navigation had consumed *all* pointer clicks. `handle_primary_click()` therefore never received the top-level Game Canvas, Pixel, Animation, etc. tab clicks, File/Edit/World menus or right-dock clicks outside the Assets content. Fix: skip canvas navigation but leave the primary-click router active; the existing `handle_assets_workspace_click()` continues consuming its own content rectangle. The Tab shortcut now returns to the previously selected workspace instead of forcibly opening Pixel.
2. `apps/haven_editor_native/src/app/world_surface_editor.rs` paints the overview from `SemanticWorldBakeV1` using `draw_rectangle` and `semantic_world_map_color`. When a major landmass is opened, `draw_scene_surface_into_rect` paints `scene_tile_color` rectangles for the materialized `SceneMap` tiles. At high zoom this is **still a schematic** and cannot turn into LPC art just by zooming. Actual atlas-backed tiles, tuples, cliffs, and objects belong to the *different* `draw_scene_tilemap` + `EditorTextureSet` path in `draw_scene_views.rs` and `scene_render_helpers.rs`.
3. The B02 Base World patch consolidated source identity and save/replica paths and materialized scenes using the existing generator. It did **not** connect the continuous world surface to the real atlas renderer and did **not** implement embedded PIE. The previous UI claim that zooming reached native 32 px terrain was misleading. B03 corrects the UI description, not the artwork.

## Immediate Windows acceptance

- Apply this ZIP alone after the B02 GREEN commit. Restart editor.
- Open global Assets workspace, then click Game Canvas, Pixel, Animation, Character, and back to Assets. All switches must work. Test top File menu, Save, and right-dock tabs while Assets is active. Verify clicking inside Assets still changes its subsections and does not paint underlying scenes.
- Open Assets from the world canvas, press Tab; verify it restores the world canvas rather than Pixel.
- Open World Overview, double-click mainland and zoom. Its status must honestly say *semantic tile preview*, not indicate that schematic colors are the game renderer.
- Open one materialized scene in Game Canvas and compare real LPC tile appearance. No whole-world visual parity or PIE is claimed here.

## Required next implementation: one visual world renderer

- Make the **continuous authored world** the one view, with region/scene/chunk data used for streaming/authoring rather than two user-visible render systems. Retain low-detail semantic geography only at overview-scale zoom; at playable zoom draw exact resolved terrain tiles, authored transitions, structural cliff recipes, visual overrides, objects and building/NPC sprites using a shared source-derived render plan and existing `EditorTextureSet` where applicable.
- Load/materialize visible world partitions on demand across boundaries. Provide explicit non-destructive loading errors; show an intentional not-yet-materialized state rather than fake art. Editor and client must consume the same authored region and asset provenance; compare the same camera/region screenshots.
- Implement real editor-hosted runtime session, rendering and input isolation for PIE separately. External development Play remains the acceptance baseline until then.

Exit criteria: Overview → zoom mainland → native textured continuous surface → select/paint across partition seam → save/reopen → Play (same visuals) → PIE Play/Stop returns to intact editor, without changing world identity. GREEN alone does not satisfy visual certification.
