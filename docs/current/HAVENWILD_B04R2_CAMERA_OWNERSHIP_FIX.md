# B04R2 — Camera ownership repair

The Windows Full Quality Gate after B04R1 failed with Rust E0596 at
`apps/haven_editor_native/src/app/world_surface_editor.rs:416`.
Macroquad 0.4 `Camera2D` does **not** implement `Clone`. In B04/B04R1,
`base_camera.clone()` cloned `&Camera2D` (the shared reference), not the
camera value. B04R1 fixed the previous E0277 double-borrow but still tried
to mutate a target behind a shared reference.

This patch creates an owned `Camera2D` by explicitly copying the scalar
and `Vec2` camera properties and viewport, and cloning only its optional
`RenderTarget` handle (which does implement `Clone`). It adjusts the owned
camera target into scene-local coordinates, calls `set_camera(&local_camera)`,
and restores the original `base_camera` after the scene draw. No world,
asset, save, PCC, or client behaviors are altered.

**Prerequisite:** B04 and B04R1 are already applied; do not reapply them.
Place this ZIP unextracted beside HavenwildTools.cmd and run PCC Option 1.
It is an incremental patch, not a cumulative replacement for B04.

**Verification:** Packaging and exact-preimage checks were run while creating
the ZIP. The Windows Rust compile and visual editor acceptance test must be
performed through the PCC and the application; they were not run here.
