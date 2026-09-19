# B48R28B | Havenwild experimental renderer and editor rebuild, first executable candidate

## Source and lineage

- Source of truth checked first: GitHub `shifty81/Havenwild`, `experimental` HEAD `16d3051b49511b0eab0cb93c3013ba9bfeb302f7` (B48R28A GREEN commit message). The actual Windows gate was not repeated by this pass.
- Companion public dependency: `shifty81/ForgeGUI_Core` commit `eafa8e78efd54142a19e66d8be7b7d3985af23d2`, v0.4.8, Rust MSRV 1.95. `forge_gui_shell`, `forge_gui_chrome`, `forge_gui_theme` are consumed by git SHA; the candidate uses the original public `ForgeShellContent` contract and `show_application_shell` function.
- Confirmed library compatibility in current official `bevy_egui` documentation: Bevy 0.19 / bevy_egui 0.42 (both use egui 0.36 for pinned ForgeGUI shell). Official `bevy_egui` render-to-image-widget example was used to select the off-screen Bevy `RenderTarget::Image` -> `EguiUserTextures` -> egui image design. See https://github.com/vladbat00/bevy_egui/blob/v0.42.0/examples/render_to_image_widget.rs .
- Current Havenwild root `Cargo.toml` retains Macroquad; `haven_render`, `haven_sim`, native editor, mapper are still Macroquad-connected. Nothing in the current root Cargo graph changes.

## Deliverable in this cumulative root-drop ZIP

`experiments/haven_bevy_candidate/` is a real new candidate Rust application, **an isolated Cargo workspace**, with Bevy 0.19, Bevy egui 0.42 and the actual pinned ForgeGUI shell. Its center panel renders an original ElizaWy source PNG using a Bevy off-screen GPU camera and registers the render target in egui. It also includes a source library, floatable inspector, semantic-fixture evidence panel, Activity panel and explicit non-certification status. The source selection is pixel-coordinate-only, with no invented terrain roles or writes.

The original source PNG is **not included in this patch**; this is intentional. Source intake takes the user's original `Terrain.zip`, checks ZIP integrity and the exact PNG SHA-256 and credits member, stages bytes only inside the candidate ignored folder, and writes a local receipt. The app checks the SHA and receipt again at startup. The actual Havenwild `content/worldgen/scenes/terrain_acceptance/river_scene_v1.json` is read directly from the root and validated as a complete semantic grid; only semantics are listed. No fake 'source-exact summer scene' is generated.

This proves more than a speculative architecture JSON **only when the Windows application actually builds and renders**. At handoff we cannot call it a passing renderer gate because Cargo/Rust and a Windows GPU runtime are absent from this execution environment. Python staging and unit tests are actual tests, not rendering certification.

## One-command preparation and candidate build (PowerShell, project root)

```powershell
py -3 experiments/haven_bevy_candidate/tools/prepare_source.py --terrain-zip "C:\path\to\original\Terrain.zip"
cd experiments/haven_bevy_candidate
cargo check
cargo run
```

Run via the project's existing internal PCC build/validation workflow for actual certification; these steps are isolated candidate smoke commands, **not** a new PCC. Do not commit the source staging directory, receipts, generated caches or `target/`.

## Bounded three-pass development / acceptance

| Pass | Actual implementation | Gate (must have real receipts) |
|---|---|---|
| R28B | Original-sheet source hash, semantic fixture input, real Bevy render-to-egui via ForgeGUI, inspector docking | Windows build, launch, correct source pixels, resizing, panel floating, no canonical writes. Current package creates candidate; Windows gate pending. |
| R28C | Reuse Havenwild `SurfaceTerrainRecipeV1`, `AuthoredSurfaceDrawPlanV2`, source-exact recipe compiler and canonical world document; real scene render, picking, command bus with revision, save and reopen | Same exact scene rendered in old/new with intentional differences documented, overlay/collision evidence, isolated copy only. |
| R28D | Actual headless authoritative sim + game client session, embedded/detached runtime transport, revisioned live updates, stop/discard | Actual-game scene, collision, animation, input, save isolation, PCC full gate, diagnostic bundle and rollback. |

Preserve existing fixtures, history, authored maps, assets, gameplay, original graphics and approvals across these passes. Source-exact visual approval is separate from general build/functional certification.

## Full rebuild scope, with responsibility boundaries

- **ForgeGUI owns:** chrome, themes, docking/floating, layout persistence, surface registration, resize and pointer/keyboard focus. Where needed, extend ForgeGUI itself via pinned reviewed changes instead of duplicating window management in Havenwild.
- **Havenwild owns:** project/document identity, selection, commands, undo/save/versioning, source provenance and certification, terrain/height/hydrology, animation/prefabs, gameplay rules, authoritative multiplayer/save data, portable estate semantics.
- **Bevy owns when proven:** main window/event loop, GPU render targets, 2D rendering/assets, candidate ECS and scheduling. Never push Bevy handles, egui IDs or crate-native scene types into Havenwild's persisted schema.
- **Existing PCC owns:** root patch inbox/approval, build/test, DebugBundle, Git, releases, rollback, and trusted gate receipts. The candidate does not launch its own update engine.
- **Tiled/LDtk:** read-only import adapters later; neither becomes a second world/asset authority. Keep original ElizaWy verification and source-exact multi-cell recipes; no automatic fabricated terrain mapping.

## Explicit blockers and honest status

1. This B48R28B app is a **source atlas preview**, not yet a semantic Havenwild scene renderer. Its semantic panel loads a real scene but visualizes no guessed mapping. It is not PIE.
2. The complete ElizaWy original library is not installed in the source rollup; the approved `Terrain.zip` sheet must be provided locally. No root source assets were overwritten.
3. Cargo/Rust toolchain and GPU/Windows testing are not available in this environment. Code and dependency versions are pinned and source-based API review performed, but Rust compilation has not been validated.
4. No Macroquad retirement, root Cargo rewiring, game simulation replacement, or deployment may be inferred from this pass. Do not replace B48R28A GREEN or promote this candidate without real PCC proof.
5. Prior B48R26–R28A entries in this ZIP are carried **unchanged** for cumulative patch continuity. This is not a complete source rollup; it is a cumulative PCC-compatible patch based on B48R28A experimental.
