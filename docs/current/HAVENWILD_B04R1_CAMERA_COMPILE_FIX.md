# B04R1 — Camera compiler fix

Fix the Macroquad `set_camera` call at `world_surface_editor.rs:417` by passing `local_camera` rather than `&local_camera`. The local variable is already borrowed because it is cloned from `base_camera: &Camera2D`; borrowing it again forms `&&Camera2D` and triggers `error[E0277]`. This patch changes only that call site.

Prerequisite: B04 applied. Place this ZIP unextracted in the repository root and run PCC Full Quality Gate. Rust compilation and runtime behavior still require Windows verification.
