# Havenwild Editor Orientation + Build Logging Hotfix

## Fixed

- Replaced the native editor canvas use of `Camera2D::from_display_rect` with an explicit camera matching the runtime's positive-Y orientation.
- The Scene Map and Scene Rectangles canvases now share the same orientation as the running game.
- Canvas hit testing continues through the same camera, so clicks, selection, painting, and object placement follow the corrected view.
- Added a unit guard requiring positive X/Y editor camera zoom.
- Updated the camera regression validator to forbid returning to `from_display_rect` in the native canvas.
- Corrected the two `cargo fmt --check` differences reported by the workstation.
- Added automatic PowerShell transcript logs under `logs/` for every `tools/build/Build.ps1`/`tools/build/Build.cmd` run.
- `tools/build/Build.cmd` now pauses when launched without arguments, allowing double-click builds to display their final status.
- Documented the correct Git Bash commands (`./tools/build/Build.sh ...`).

## Workstation verification

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
./tools/build/Build.sh validate
./tools/build/Build.sh editor
./tools/build/Build.sh game
```

In PowerShell, replace `./tools/build/Build.sh` with `.\\tools/build/Build.cmd`.
