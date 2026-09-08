# Havenwild Editor Architecture Normalization — Pass 48A

Pass 48A is a behavior-preserving architecture pass performed before expanding the infinite-canvas authoring toolset. Its purpose is to stop the native editor, shared editing logic, renderer, networking contracts, and runtime developer tools from collapsing into a single dependency chain.

## Resulting ownership

```text
apps/haven_editor_native
    Native Macroquad window, docked layout, workspace input, canvas camera,
    canvas rendering, scene authoring UI, and application lifetime.

crates/haven_editor
    Headless project/editor facade: inspection, validation, project files,
    scene-edit services, and compatibility exports.

crates/haven_authoring
    Presentation-neutral commands, diagnostics, stable selection groundwork,
    and future transaction contracts.

crates/haven_render
    Shared rendering helpers. May consume haven_authoring diagnostics but does
    not depend on haven_editor or the native application.

crates/haven_net
    Authority and replication envelopes. May consume haven_authoring commands
    but does not depend on haven_editor or the native application.
```

## Native editor decomposition

The former `crates/haven_editor/src/main.rs` contained 2,663 lines and mixed application lifetime, state, input, hit testing, canvas navigation, scene commands, panel rendering, and helper rendering.

It is replaced by:

```text
apps/haven_editor_native/src/main.rs
apps/haven_editor_native/src/app/mod.rs
apps/haven_editor_native/src/app/input.rs
apps/haven_editor_native/src/app/canvas_controller.rs
apps/haven_editor_native/src/app/canvas_camera.rs
apps/haven_editor_native/src/app/canvas_view.rs
apps/haven_editor_native/src/app/draw.rs
apps/haven_editor_native/src/app/scene_authoring.rs
apps/haven_editor_native/src/app/region_commands.rs
apps/haven_editor_native/src/app/render_helpers.rs
```

The executable entrypoint is now intentionally tiny. The current visual behavior from Pass 47 remains in place while future selection, layer, clipboard, and transaction systems gain explicit homes.

## Neutral authoring contracts

`haven_authoring` now owns:

- `EditorCommand`, command targets/payloads, and the current compatibility undo bus.
- `InspectorReport`, allowing render code to display diagnostics without depending on the editor crate.
- `EditorSelection`, `SelectionItem`, `ObjectId`, and `TransitionId` groundwork for the stable-ID selection migration.

`haven_editor::command_bus` remains as a compatibility re-export so current callers and saves can migrate incrementally.

## Dependency corrections

Corrected:

```text
haven_render -> haven_editor
haven_net    -> haven_editor
```

To:

```text
haven_render -> haven_authoring
haven_net    -> haven_authoring
```

The game still depends on `haven_editor` for actual editing and validation services, while neutral command and inspector types are imported directly from `haven_authoring`.

## Guardrails

The new authoritative architecture validator:

- scans every Rust file in `apps/` and `crates/`;
- limits new application entrypoints to 150 lines;
- applies a default 750-line ceiling to new Rust modules;
- records existing oversized files in an explicit no-growth allowlist;
- verifies that the headless editor has no Macroquad dependency;
- rejects renderer/network dependencies on `haven_editor`;
- verifies the normalized native editor module layout.

Existing debt is stored in:

```text
content/architecture/rust_file_size_allowlist.json
```

Each exception has a locked temporary maximum, a smaller target, and a reason. An existing exception may shrink, but it must not silently grow.

## Build and validation entrypoints

Windows:

```powershell
.\tools/build/Build.cmd validate
.\tools/build/Build.cmd check
.\tools/build/Build.cmd editor
```

Linux/macOS:

```bash
./tools/build/Build.sh validate
./tools/build/Build.sh check
./tools/build/Build.sh editor
```

Direct validation:

```bash
python3 tools/automation/validation/validate.py all
```

## KEEP / REWRITE / DEFER / NEXT

| Area | Decision | Status |
|---|---|---|
| Pass 47 permanent canvas behavior | KEEP | Preserved in the native app |
| Native editor application lifetime | REWRITE | Extracted to `apps/haven_editor_native` |
| Command/diagnostic ownership | REWRITE | Moved to `haven_authoring` with compatibility exports |
| Renderer/network editor dependency | REWRITE | Inversion removed |
| Full-world snapshot undo | DEFER | Kept temporarily for compatibility |
| `foundation.rs` world model monolith | DEFER | Pass 48B |
| `SceneMap.id: SceneId` | DEFER | Pass 48B registry migration |
| Stable object/transition IDs in runtime storage | NEXT | Pass 48C |
| Typed transactions and gesture coalescing | NEXT | Pass 48D |
| Marquee, move, clipboard, fill, rectangle tools | NEXT | Pass 49 after foundations |

## Build note

This source was structurally and contract validated in the packaging environment. A full Cargo compile must still be run on the normal Rust development machine because the packaging environment does not contain Cargo or Rustc.
