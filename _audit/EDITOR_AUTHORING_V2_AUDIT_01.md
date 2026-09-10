# Havenwild Editor / Authoring V2 Audit — HW-EDITOR-AUDIT-01

Baseline: `HW-FORGE-ADAPTER-01` / `e21419aa8f2f9d748f053be604c34a6ce819ad3c`  
Scope: native editor + F3/runtime authoring surfaces  
Behavior change in this pass: **none**

## Result

The current editor is not discarded. It contains the correct long-term pieces, but the authoring experience is split across legacy viewport modes, parallel Scene/World tool state, several palette/browser generations, and a second runtime/F3 mini-editor. This pass freezes the disposition of every scoped module before structural changes begin.

The machine-readable authority is:

`content/editor/architecture/editor_authoring_v2_audit_manifest_v0_1.json`

It classifies **106 native editor source files** and **30 runtime/F3 authoring files**.

Native disposition: ADAPT=50, DELETE_LATER=1, KEEP=33, MERGE=22.  
Runtime/F3 disposition: ADAPT=9, DEPRECATE=5, KEEP=11, MERGE=5.

## Locked target

Havenwild moves toward a GameMaker/LDtk-style authoring workflow centered on one Game Canvas. World and Scene remain meaningful edit scopes, but they no longer own separate copies of the tool system. `UniversalTool`, `CanvasLayerKind`, `AuthoringSession`, stable document/resource identity, and shared `haven_authoring` commands become the convergence points.

The permanent creator workflow is:

`Source Atlas -> Semantic Asset -> Context Palette -> Game Canvas -> Shared Authoring Transaction -> Save / PIE / Runtime`

The Game Canvas permanently supports both semantic/autotile painting and exact raw tile/region placement. Exact placement is a supported authoring mode, not an emergency hack. Approved manual cliff/ramp/cave/building arrangements can be saved as reusable patterns/prefabs/PCG exemplars.

Spawn placement becomes a first-class tool supporting Player Start, Play From Here, NPCs, population spawners, animals, resources, encounters, transition destinations and PCG anchors.

## P0 audit findings

1. **Legacy state still owns the new session.** `authoring_session.rs` and `document_authority.rs` are strong V2 migration seams, but they currently snapshot state owned elsewhere rather than owning it.
2. **Scene and World duplicate authoring vocabulary.** The editor contains parallel edit-tool and layer-mode enums in addition to `UniversalTool` and `CanvasLayerKind`.
3. **Layer inference still guesses from names.** Stamps can be classified by strings such as `water`, `pond`, `cliff`, `house`, `roof`, `wall`, etc. Catalog V2 must provide typed semantic metadata instead.
4. **Asset sources and usable assets are still mixed.** `AssetsStudio` is a useful authority-oriented start, but normal creator palettes must show semantic subassets; source sheets belong under Sources/Atlas Inspector.
5. **F3 is not actually lightweight.** The runtime currently enables both developer mode and build mode when F3 is toggled. F3 V2 must toggle inspection/diagnostics only; Runtime Edit is opened separately.
6. **F3 duplicates editing authority.** Runtime-specific map/object/world-paint/rules panels must become presentations over shared authoring commands.
7. **Spawn authoring is incomplete.** A current scene-spawn hotkey exists, but there is no unified typed spawn/anchor workflow.
8. **Manual authoring and PCG are not yet one vocabulary.** Existing direct-visual and exemplar infrastructure should become the permanent manual-to-PCG bridge.

## Disposition rules

- **KEEP** — already a suitable canonical owner or backend contract.
- **MERGE** — useful functionality, but its current module should fold into another canonical owner.
- **ADAPT** — keep the module and refactor it to Authoring V2.
- **DEPRECATE** — compatibility/regression only; no new features.
- **DELETE_LATER** — detached/superseded code; remove only after unique behavior is verified migrated.

No file is deleted by this audit pass.

## Native editor module matrix

| File | Disposition | Target owner | Priority |
|---|---|---|---|
| `animation_studio.rs` | **ADAPT** | Animation Workspace | P2 |
| `animation_studio_input.rs` | **ADAPT** | Animation Workspace | P2 |
| `animation_studio_render.rs` | **ADAPT** | Animation Workspace | P2 |
| `animation_studio_runtime_context.rs` | **KEEP** | Animation Workspace | P2 |
| `asset_browser_ui.rs` | **KEEP** | Asset Catalog V2 / Atlas Inspector | P0 |
| `assets_studio.rs` | **ADAPT** | Asset Catalog V2 / Atlas Inspector | P0 |
| `authoring_publish.rs` | **MERGE** | Authoring Session / Document / Command Spine | P0 |
| `authoring_session.rs` | **KEEP** | Authoring Session / Document / Command Spine | P0 |
| `asset_hot_reload.rs` | **KEEP** | Asset Catalog V2 / Atlas Inspector | P0 |
| `asset_palette_panel.rs` | **MERGE** | Asset Catalog V2 / Atlas Inspector | P0 |
| `atlas_render.rs` | **ADAPT** | Asset Catalog V2 / Atlas Inspector | P0 |
| `autotile_authoring.rs` | **ADAPT** | Terrain/Structure Authoring V2 | P0 |
| `autotile_render.rs` | **ADAPT** | Terrain/Structure Authoring V2 | P0 |
| `authoring_changeset.rs` | **MERGE** | Authoring Session / Document / Command Spine | P0 |
| `bulk_result.rs` | **MERGE** | Editor V2 | P1 |
| `building_instance_preview.rs` | **ADAPT** | Inspector / Content Authoring | P1 |
| `brush_authoring.rs` | **ADAPT** | Game Canvas Core | P0 |
| `brush_palette_drawer.rs` | **MERGE** | Game Canvas Core | P0 |
| `canvas_camera.rs` | **KEEP** | Game Canvas Core | P0 |
| `canvas_controller.rs` | **ADAPT** | Game Canvas Core | P0 |
| `canvas_layers.rs` | **ADAPT** | Game Canvas Core | P0 |
| `canvas_tool_rack.rs` | **ADAPT** | Game Canvas Core | P0 |
| `canvas_view.rs` | **KEEP** | Game Canvas Core | P0 |
| `canvas_workspace.rs` | **KEEP** | Game Canvas Core | P0 |
| `character_studio.rs` | **ADAPT** | Character Workspace | P2 |
| `character_studio_layout.rs` | **ADAPT** | Character Workspace | P2 |
| `character_studio_runtime_ext.rs` | **ADAPT** | Character Workspace | P2 |
| `clipboard_tools.rs` | **KEEP** | Game Canvas World/Scene | P0 |
| `collision_authoring.rs` | **ADAPT** | Inspector / Content Authoring | P1 |
| `command_registry.rs` | **ADAPT** | Authoring Session / Document / Command Spine | P0 |
| `dev_client_bridge.rs` | **MERGE** | PIE / Runtime Bridge | P1 |
| `development_session.rs` | **KEEP** | PIE / Runtime Bridge | P1 |
| `direct_visual_authoring.rs` | **ADAPT** | Game Canvas Core | P0 |
| `document_authority.rs` | **KEEP** | Authoring Session / Document / Command Spine | P0 |
| `document_lifecycle.rs` | **KEEP** | Authoring Session / Document / Command Spine | P0 |
| `document_tabs.rs` | **ADAPT** | Authoring Session / Document / Command Spine | P0 |
| `draw.rs` | **ADAPT** | GameMaker-style Editor Shell | P0 |
| `draw_scene_views.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `editor_help.rs` | **ADAPT** | GameMaker-style Editor Shell | P1 |
| `editor_menu.rs` | **ADAPT** | GameMaker-style Editor Shell | P1 |
| `editor_settings.rs` | **ADAPT** | GameMaker-style Editor Shell | P1 |
| `editor_text.rs` | **KEEP** | GameMaker-style Editor Shell | P1 |
| `editor_theme.rs` | **KEEP** | GameMaker-style Editor Shell | P1 |
| `editor_types.rs` | **MERGE** | Authoring Session / Document / Command Spine | P0 |
| `enclosed_scene_authoring.rs` | **ADAPT** | Inspector / Content Authoring | P1 |
| `game_canvas_ui.rs` | **ADAPT** | UI Authoring in Game Canvas | P1 |
| `gameplay_layer_authoring.rs` | **ADAPT** | Inspector / Content Authoring | P1 |
| `gui_authority.rs` | **KEEP** | UI Authoring in Game Canvas | P1 |
| `gui_controls.rs` | **KEEP** | UI Authoring in Game Canvas | P1 |
| `gui_studio.rs` | **DELETE_LATER** | Game Canvas UI | P2 |
| `input.rs` | **ADAPT** | GameMaker-style Editor Shell | P0 |
| `island_authoring.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `island_workspace.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `logic_studio.rs` | **ADAPT** | Logic Workspace | P2 |
| `mod.rs` | **ADAPT** | Authoring Session / Document / Command Spine | P0 |
| `object_inspector.rs` | **ADAPT** | Inspector / Content Authoring | P1 |
| `object_inspector_geometry.rs` | **KEEP** | Inspector / Content Authoring | P1 |
| `pcg_exemplar_authoring.rs` | **ADAPT** | Terrain/Structure Authoring V2 | P0 |
| `pixel_animation_bridge.rs` | **KEEP** | Pixel Workspace | P2 |
| `pixel_color_panel.rs` | **KEEP** | Pixel Workspace | P2 |
| `pixel_context_layout.rs` | **MERGE** | Pixel Workspace | P2 |
| `pixel_layer_input.rs` | **KEEP** | Pixel Workspace | P2 |
| `pixel_layer_rail.rs` | **ADAPT** | Pixel Workspace | P2 |
| `pixel_library_panel.rs` | **ADAPT** | Pixel Workspace | P2 |
| `pixel_new_document.rs` | **KEEP** | Pixel Workspace | P2 |
| `pixel_new_document_input.rs` | **MERGE** | Pixel Workspace | P2 |
| `pixel_studio.rs` | **ADAPT** | Pixel Workspace | P2 |
| `pixel_studio_input.rs` | **ADAPT** | Pixel Workspace | P2 |
| `pixel_studio_layout.rs` | **KEEP** | Pixel Workspace | P2 |
| `pixel_studio_render.rs` | **ADAPT** | Pixel Workspace | P2 |
| `prepared_canvas_composition.rs` | **KEEP** | Editor V2 | P1 |
| `production_tools.rs` | **ADAPT** | PIE / Runtime Bridge | P1 |
| `region_commands.rs` | **MERGE** | Game Canvas Routes/World | P1 |
| `render_helpers.rs` | **KEEP** | GameMaker-style Editor Shell | P1 |
| `resource_context_bridge.rs` | **KEEP** | PIE / Runtime Bridge | P1 |
| `right_dock.rs` | **ADAPT** | GameMaker-style Editor Shell | P1 |
| `scene_asset_context.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `scene_authoring.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `scene_bank_workspace.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `scene_outliner.rs` | **ADAPT** | Game Canvas World/Scene | P0 |
| `scene_render_helpers.rs` | **KEEP** | Game Canvas World/Scene | P0 |
| `selection_controller.rs` | **KEEP** | Game Canvas World/Scene | P0 |
| `shared_palette.rs` | **MERGE** | Game Canvas Core | P0 |
| `sound_studio.rs` | **ADAPT** | Sound Workspace | P2 |
| `sprite_canvas_authority.rs` | **KEEP** | Pixel Workspace | P2 |
| `sprite_workspace.rs` | **ADAPT** | Pixel Workspace | P2 |
| `stamp_inspector_panel.rs` | **MERGE** | Inspector / Content Authoring | P1 |
| `structural_cliff_preview.rs` | **ADAPT** | Terrain/Structure Authoring V2 | P0 |
| `terrain_material_browser.rs` | **MERGE** | Asset Catalog V2 / Atlas Inspector | P0 |
| `terrain_tile_variant_authoring.rs` | **ADAPT** | Asset Catalog V2 / Atlas Inspector | P0 |
| `terrain_transition_workbench.rs` | **ADAPT** | Terrain/Structure Authoring V2 | P0 |
| `tool_registry.rs` | **KEEP** | Editor V2 | P1 |
| `tooltip_overlay.rs` | **KEEP** | GameMaker-style Editor Shell | P1 |
| `transform_gizmo.rs` | **KEEP** | Game Canvas Core | P0 |
| `ui_shell.rs` | **ADAPT** | GameMaker-style Editor Shell | P0 |
| `unified_asset_browser.rs` | **KEEP** | Asset Catalog V2 / Atlas Inspector | P0 |
| `workspace_chrome.rs` | **ADAPT** | GameMaker-style Editor Shell | P0 |
| `workspace_shell.rs` | **ADAPT** | GameMaker-style Editor Shell | P0 |
| `world_asset_pixel_bridge.rs` | **ADAPT** | Asset Catalog V2 / Atlas Inspector | P0 |
| `world_canvas_context.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `world_surface_authoring.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `world_surface_authoring_geometry.rs` | **KEEP** | Game Canvas World/Scene | P0 |
| `world_surface_authoring_tests.rs` | **KEEP** | Game Canvas World/Scene | P0 |
| `world_surface_authoring_ui.rs` | **MERGE** | Game Canvas World/Scene | P0 |
| `world_surface_editor.rs` | **ADAPT** | Game Canvas World/Scene | P0 |
| `world_surface_structural_authoring.rs` | **ADAPT** | Game Canvas World/Scene | P0 |


## F3 / runtime authoring matrix

| File | Disposition | Target owner | Priority |
|---|---|---|---|
| `asset_reference_browser_panel.rs` | **DEPRECATE** | Asset Catalog V2 / Atlas Inspector | P0 |
| `client_controls.rs` | **ADAPT** | Runtime Input Actions | P1 |
| `development_launch.rs` | **KEEP** | PIE / Development Launch | P0 |
| `development_live_bridge.rs` | **KEEP** | PIE / Runtime Bridge | P0 |
| `development_resource_context.rs` | **KEEP** | Shared Resource Context | P0 |
| `editor_state.rs` | **DEPRECATE** | Runtime Developer Session | P0 |
| `gameplay_tool_runtime.rs` | **KEEP** | Gameplay Runtime | P1 |
| `map_edit_runtime.rs` | **MERGE** | Shared Terrain/Structure Authoring | P0 |
| `object_edit_runtime.rs` | **MERGE** | Shared Object Authoring | P0 |
| `render_telemetry.rs` | **KEEP** | Runtime Diagnostics | P0 |
| `runtime_commands.rs` | **MERGE** | haven_authoring Command/Transaction Spine | P0 |
| `runtime_diagnostics.rs` | **KEEP** | Runtime Diagnostics | P0 |
| `runtime_draw.rs` | **ADAPT** | Runtime Presentation | P0 |
| `runtime_editor_draw.rs` | **ADAPT** | F3 Developer Overlay / Runtime Edit Mode | P0 |
| `runtime_editor_shell.rs` | **ADAPT** | F3 Developer Overlay Shell | P0 |
| `runtime_hud.rs` | **KEEP** | Gameplay HUD | P1 |
| `runtime_input.rs` | **ADAPT** | Runtime Input Router | P0 |
| `runtime_performance_snapshot.rs` | **KEEP** | Runtime Diagnostics | P0 |
| `runtime_persistence.rs` | **KEEP** | Runtime Persistence | P0 |
| `runtime_scene_navigation.rs` | **ADAPT** | Runtime Navigation / Spawn | P0 |
| `terrain_debug_overlay.rs` | **ADAPT** | F3 Diagnostics | P0 |
| `transition_edit_runtime.rs` | **MERGE** | Shared Transition Authoring | P1 |
| `transition_rule_editor_panel.rs` | **DEPRECATE** | Native Advanced Terrain Tool | P1 |
| `transition_rule_inspector_overlay.rs` | **ADAPT** | F3 Diagnostics | P1 |
| `transition_rule_preview_overlay.rs` | **ADAPT** | F3 Diagnostics | P1 |
| `world_paint_editor_draw.rs` | **DEPRECATE** | Runtime Edit Palette | P0 |
| `world_paint_editor_panel.rs` | **MERGE** | Shared Terrain Authoring | P0 |
| `world_paint_lifecycle.rs` | **KEEP** | Terrain Persistence | P0 |
| `world_paint_render_binding.rs` | **KEEP** | Terrain Render Binding | P0 |
| `world_rules_runtime.rs` | **DEPRECATE** | Native Advanced Rules / Shared Inspector | P1 |


## Migration waves after this audit

**E2 — Authoring spine and shell.** Promote AuthoringSession/DocumentAuthority, unify command context, remove duplicate tool/layer state authority, and establish the simplified GameMaker-style shell contract.

**E3 — Game Canvas core.** One tool rail, one layer tree, one contextual palette, camera/selection/clipboard, exact manual overrides and spawn tool.

**E4 — World/Scene convergence.** World and Scene become scopes/views of one Game Canvas authoring system. Object/building/zone/transition/spawn edits use the same transactions.

**E5 — Asset Catalog V2.** Source Sheets -> Semantic Assets -> Runtime Assets; Atlas Inspector; cropped/animated subasset previews; typed semantic layers and placement metadata.

**E6 — Terrain/Structure V2.** Metadata-driven autotile/material rules, exact raw placement, structural patterns, cliffs/ramps/ladders/caves/bridges and approved PCG exemplars.

**E7 — Specialized workspaces.** Pixel, Animation, Character, Logic, Sound and UI become document workspaces attached to the same resource/document/session spine.

**E8 — PIE + F3 V2.** Lightweight F3 overlay, explicit Runtime Edit mode, Play From Here, cached diagnostics and parity certification against native editor operations.

## Pass 2 entry gate

Do not start by changing terrain visuals. Pass 2 should first create the canonical Authoring Context/Command spine and migrate the duplicated tool/layer/session state behind it. Existing GREEN runtime behavior remains the regression oracle until parity tests say otherwise.
