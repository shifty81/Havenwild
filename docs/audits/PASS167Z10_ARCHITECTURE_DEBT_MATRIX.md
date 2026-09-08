# Pass 167Z10 Architecture Debt Matrix

Folder and tooling normalization is complete. These Rust files remain intentionally locked against growth and are the next code-decomposition lane. The allowlist records the current baseline; it does not declare these files finished.

| File | Current lines | Target | Extraction direction |
|---|---:|---:|---|
| `crates/haven_core/src/foundation.rs` | 1796 | 700 | Core tile/object/map aggregate; extract terrain definitions, map state, and object contracts into domain modules. |
| `crates/haven_game/src/client_character_frontend_draw.rs` | 928 | 500 | Character frontend drawing aggregate; split portrait/vitals, creator preview, and in-world character presentation. |
| `crates/haven_game/src/client_frontend.rs` | 2065 | 500 | Client frontend coordinator; split title flow, world creation, character creation, pause, and runtime HUD state. |
| `crates/haven_game/src/player_inventory_ui.rs` | 2043 | 500 | Inventory UI aggregate; split model, layout, interaction, tooltip, equipment, and crafting views. |
| `crates/haven_game/src/runtime_draw.rs` | 818 | 500 | Runtime draw coordinator; continue extracting discrete render passes and frame assembly. |
| `crates/haven_game/src/runtime_terrain_pass.rs` | 846 | 500 | Terrain render-pass aggregate; split visibility planning, transition resolution, and submission. |
| `crates/haven_game/src/terrain_render.rs` | 1050 | 500 | Terrain rendering helpers; split source binding, material resolution, transition ownership, and diagnostics. |
| `apps/haven_editor_native/src/app/mod.rs` | 762 | 500 | Native editor application coordinator; split startup/session, workspace routing, and panel registration. |
| `apps/haven_editor_native/src/app/object_inspector.rs` | 930 | 500 | Inspector aggregate; split property models, editors, validation, and presentation. |
| `apps/haven_editor_native/src/app/pixel_studio_input.rs` | 839 | 500 | Pixel Studio input aggregate; split tool dispatch, selection, transforms, and timeline input. |
| `apps/haven_editor_native/src/app/pixel_studio_render.rs` | 964 | 500 | Pixel Studio rendering aggregate; split canvas, overlays, timeline, panels, and tool previews. |
| `apps/haven_editor_native/src/app/render_helpers.rs` | 893 | 500 | Native editor helper aggregate; split shared primitives, text/layout, and domain-specific helpers. |

## Order

1. `client_frontend.rs` and `player_inventory_ui.rs` — highest UI iteration cost.
2. `terrain_render.rs` and `runtime_terrain_pass.rs` — highest terrain-debugging risk.
3. Pixel Studio input/render and native inspector — highest editor workflow cost.
4. Remaining coordinators and shared helpers.

Each extraction should preserve behavior, add module-level tests, and lower the temporary maximum in `content/architecture/rust_file_size_allowlist.json`.

## Editor command metadata normalization

The command bus has typed transactions, gesture coalescing, preview state, validation result storage, and world-aware undo/redo. The richer execution metadata declared by `editor_command_contract_v1.json` is still pending extraction into Rust types. Pass 167Z10 marks this honestly as transitional instead of allowing a historical string validator to claim the feature is complete.
