# World Paint Mirror + egui Pixel Editor Host Spec Pass 30

This pass adds horizontal and vertical mirror mode to the world paint backend and specs the future egui-hosted Lite Pixel Editor panel.

## Mirror paint behavior

The canonical gameplay grid remains `32x32`. Mirror mode duplicates the brush center over the scene axes:

- horizontal mirror: `mirrored_x = scene_width - 1 - x`
- vertical mirror: `mirrored_y = scene_height - 1 - y`
- both enabled: four-way paint, deduplicated when centers overlap

The paint backend writes the same deterministic operation shape for original and mirrored centers. The host/server can store mirror flags and the resolved center list, while clients derive visual shoreline/foam/variation overlays from the same manifests.

## In-game Paint tab controls

- `H` toggles horizontal mirror
- `V` toggles vertical mirror
- `A` toggles autotile refresh
- `J/K` cycle material family
- `[` / `]` cycle subcell mode
- `P` cycles target layer
- `R` matches target layer to material family

## egui Lite Pixel Editor host panel

The egui panel spec lives at:

```text
content/editor/pixel_editor/egui_pixel_editor_host_panel_v0_1.json
```

It defines the future pixel editor as a panel host rather than a new monolith. Ownership boundaries:

- `haven_game`: panel wiring/runtime preview only
- `haven_editor`: commands, undo/redo, inspectors, validation, tool models
- `haven_assets`: tile records, atlases, donor/reference catalogs, import/bake metadata
- `haven_world`: deterministic paint/autotile/subcell logic
- `haven_render`: preview composition and grid rendering helpers

## Validation

- `tools/automation/validation/checks/terrain/Validate-WorldPaintMirrorAndPixelEditorV36.py`
- `tools/automation/validation/checks/misc/Validate-AntiMonolithGuardrailsV37.py`
