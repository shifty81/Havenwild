# Pass 162G Native UI Consolidation Audit

Direct rectangle drawing remains valid for canvas and world visualization.
Interactive chrome should migrate toward shared components.

## Remaining direct rectangle calls

- `render_helpers.rs`: 24
- `autotile_render.rs`: 11
- `canvas_view.rs`: 10
- `animation_studio_render.rs`: 4
- `island_workspace.rs`: 4
- `pixel_studio_render.rs`: 4
- `asset_palette_panel.rs`: 3
- `scene_bank_workspace.rs`: 3
- `asset_intake_panel.rs`: 2
- `draw.rs`: 2
- `draw_scene_views.rs`: 2
- `pixel_new_document.rs`: 2
- `animation_studio.rs`: 1
- `asset_library_panel.rs`: 1
- `autotile_authoring.rs`: 1
- `editor_menu.rs`: 1
- `mod.rs`: 1
- `object_inspector.rs`: 1
- `pixel_layer_panel.rs`: 1
- `pixel_studio_input.rs`: 1
- `world_canvas_context.rs`: 1

## Consolidated in this pass

- Workspace tabs
- Standard, primary, quiet, destructive, and disabled action tones
- Menu dropdown rows
- Save All primary action
- Modal text fields
- Modal primary and cancel actions

## Next migration priority

1. Object and stamp inspectors
2. Autotile authoring controls
3. Remaining Pixel and Animation inspector fields
4. Island workspace action groups