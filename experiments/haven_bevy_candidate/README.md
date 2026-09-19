# Havenwild B48R28B — isolated Bevy / ForgeGUI source-preview candidate

**Candidate only. NOT the game, NOT the World Editor, NOT a replacement renderer yet.** This optional app uses a real Bevy 0.19 off-screen render target containing the **original** `Terrain/terrain_summer.png` source sheet, displayed in the **actual pinned ForgeGUI shell** through `bevy_egui` 0.42 / egui 0.36. It reads the existing `terrain_acceptance/river_scene_v1.json` **semantics for evidence only**; it deliberately does not guess a mapping from semantic role to source pixels. Pixel selection inspects source coordinates only; there are no writes, fake edit commands, save or PIE actions.

This project is an independent `[workspace]`, **not** a Havenwild root workspace member. Current production editor, game, world, source registry, PCC and canonical saves are unchanged.

## Windows execution after applying cumulative root ZIP through the existing PCC

From the Havenwild repository root in PowerShell:

```powershell
py -3 experiments/haven_bevy_candidate/tools/prepare_source.py --terrain-zip "C:\path\to\original\Terrain.zip"
cd experiments/haven_bevy_candidate
cargo +stable check
cargo +stable run
```

Rust compiler **at least 1.95** is required by pinned ForgeGUI. Source preparation validates a specific original source PNG SHA, ZIP integrity, exact fixture dimensions, and Git branch/ancestry when present. Assets and source-receipt data are staged **only** into `.gitignore`d candidate folders and never shipped in the PCC patch. With absent `.git` metadata, the receipt says so; it cannot claim Git or PCC certification. The application verifies the original hash and receipt again at startup and fails closed if missing.

## What this demonstrates (only if actually built and launched)

1. Real Bevy GPU render-to-image (512×832 source image) shown through ForgeGUI's center surface; nearest-neighbor source sampling.
2. ForgeGUI's registered Source Library, source preview, Inspector, Scene Semantics, Activity surfaces; use Dock to float Inspector and test window resize.
3. The immutable original ElizaWy PNG and the real Havenwild river acceptance scene are consumed as distinct, correctly labeled resources.
4. The Bevy candidate dependency graph is Macroquad-free (independent workspace; the root engine still uses Macroquad).

## What is NOT proven

World terrain resolver/certified art assembly; cliff/water semantics; editor document commands; selection in world coordinates; PIXEL/animation/prefab studio migration; integrated Play-in-Editor; full game; runtime parity; Windows build; PCC Full Gate; retirement of Macroquad. Do not promote the app or use its screenshot as an approved summer scene. Do not substitute `assets/generated/**` for original licensed art.

## Actual next two bounded passes

- **R28C:** feed canonical authored world document + certified terrain draw-plan into Bevy offscreen camera, implement coordinate-picking, ForgeGUI Inspector authoring commands with expected revision, undo/save/reopen in disposable scene copy. Preserve original source hashes.
- **R28D:** run actual Havenwild authoritative host and game through the same document snapshot, record scene/asset revision ACKs, collision, screenshots, performance, reset behavior and PCC Full Gate. Only then decide renderer promotion.

The actual prepared asset file is `assets/source/Terrain/terrain_summer.png`, staged from the user-supplied archive. `evidence/source_stage.json` is local candidate evidence, **not** an art-approval or gate receipt. No additional PCC entry was created: existing root-drop intake and Full Quality Gate remain the authority.
