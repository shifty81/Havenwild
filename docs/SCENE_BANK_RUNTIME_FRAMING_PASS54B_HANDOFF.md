# Havenwild Scene Bank + Runtime Framing — Pass 54B

This pass continues from `Havenwild_UpdatedSource_WorldCanvasIslandPcgHarborPass54A_20260711.zip`.

## Completed

- Renamed native-editor workspaces to **World Routes**, **Overworld Layout**, **Scene Bank**, and **Scene Editor**.
- Added a dedicated Scene Bank workspace with a persistent infinite canvas, smooth zoom/pan, preview cards, list selection, inspector metadata, keyboard navigation, and opening into Scene Editor.
- Removed the redundant fixed Scene Bank dock from Overworld Layout, giving the island/world canvas the full viewport.
- Preserved all Pass 54A right-click PCG, island, persistence, and harbor-route workflows.
- Removed player-controlled runtime zoom while preserving the approved 115% gameplay framing.
- Added scene-bound camera clamping so scene borders stay at the screen edge and the player becomes off-center near boundaries.
- Kept native-editor zoom logic unchanged.
- Deepened nighttime darkness and moved the lighting overlay behind UI.
- Added regression tests and validation markers for fixed runtime framing, scene-edge clamping, Scene Bank separation, and dark-night presentation.

## Validation completed in this environment

- Python validation scripts compile.
- All 190 JSON files and 13 TOML files parse successfully.
- JavaScript syntax check passes.
- Rust lexical delimiter check passes across 139 Rust files.
- Architecture, content, world preset, Pass 54 through Pass 68, camera, Scene Bank, island PCG, harbor routing, asset palette, autotile, and deterministic asset-intake validators pass.

Cargo and Rustc are not installed in this container, so Rust formatting, compilation, Clippy, and unit tests remain required on the Windows Rust workstation using the commands below.

## Windows verification

```powershell
cargo fmt --all
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
.\tools/build/Build.cmd apps
```

Expected packaged outputs:

```text
Build/HavenwildClient/HavenwildClient.exe
Build/HavenwildEditor/HavenwildEditor.exe
```
