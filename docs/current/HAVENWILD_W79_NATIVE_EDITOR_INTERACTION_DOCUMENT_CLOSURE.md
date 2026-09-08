# Havenwild W79 — Native Editor Interaction & Document Closure

Baseline: **W78 Native Editor GUI Authority Cleanup**.

W79 closes the first user-facing interaction gaps on top of W78 before the Tool/Layer Rail production pass and the shared raster-authoring core.

## Locked authorities

- `document_lifecycle.rs` is the common close/reopen authority for Scene, Pixel, World, Animation, Character, Logic, Sound, Routes and Scene Bank views.
- A dirty close routes through **Save & Close / Close Without Saving / Cancel**; closing a view never deletes the project resource.
- Pixel document close retains the complete working session in recently-closed history so `Ctrl+Shift+T` can restore it.
- `editor_settings.rs` plus `WORKSPACE/editor/native_editor_settings_v0_1.json` establishes the single top-rail Settings surface.
- Tool Rail help text uses a hovered-control anchored tooltip rectangle rather than the former canvas/Layer-side placement proxy.
- Validation report rows are horizontally scissored and vertically bounded.
- Default editor text scale is reduced from 1.15 to 1.10 and shared button/control labels use the compact 12 px presentation.

## Shortcuts

- `Ctrl+S` — Save
- `Ctrl+W` — request close of the active document/view
- `Ctrl+Shift+T` — reopen the most recently closed document/view

## Deliberate W79 boundaries

W79 is a convergence/foundation pass, not the final Tool/Layer Rail or Pixel/Animation production pass. Save & Close currently delegates to the existing Save All authority. Explicit Save As adapters for untitled/new resources and native OS-window close interception remain later integration points. The Windows Full Quality Gate remains the authoritative Rust compile/test checkpoint.

## Next

W80 finishes the canonical Tool Rail and Layer Rail. W81 then extracts one raster-authoring core for Pixel Studio, Animation Studio, World Pixel Mode and Scene Pixel Mode.
