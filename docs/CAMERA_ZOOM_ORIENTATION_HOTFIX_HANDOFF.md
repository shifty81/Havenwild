# Havenwild Camera Zoom and Runtime Orientation Hotfix

> **Superseded runtime behavior:** Pass 54B keeps the native-editor smoothing/orientation fixes from this handoff, but replaces player-controlled runtime zoom with a fixed 115% gameplay camera and scene-edge clamping. See `SCENE_BANK_RUNTIME_FRAMING_PASS54B_HANDOFF.md`.

## Scope

This hotfix addresses three regressions in the supplied `havenwild-clean-source-2026-07-10(3).zip` baseline:

1. Native editor wheel zoom racing to its maximum and continuing after the user scrolls back.
2. Runtime camera wheel zoom exhibiting the same runaway behavior.
3. Runtime world/player rendering appearing vertically inverted after the new zoom camera was added.

## Root causes

### Wheel input

Both zoom paths converted every non-zero wheel sample with `signum()`. High-resolution mouse wheels and touchpads can produce fractional and inertial residual samples. Promoting each residual to a full `-1` or `+1` step repeatedly drove the zoom target to a hard limit.

### Runtime orientation

The runtime draws its world through screen-style coordinates where positive Y points downward. The newly introduced display-rectangle camera used the opposite vertical camera convention, flipping the rendered game view.

## Changes

### Native editor

- Preserves fractional wheel input rather than converting it with `signum()`.
- Clamps unusually large wheel samples to one bounded step.
- Ignores residual wheel noise below `0.05`.
- Adds a separate smoothed zoom target.
- Keeps cursor-centered zoom while the camera interpolates.
- Limits canvas zoom to 25%–300%.
- Routes toolbar zoom buttons through the same target system.
- `F` still resets/frames the active editor canvas.

### Runtime

- Preserves fractional wheel input.
- Clamps large wheel samples and ignores residual noise.
- Retains smooth interpolation between current and target zoom.
- Keeps runtime zoom limited to 95%–175%.
- Adds `Home` as a recovery shortcut that resets runtime zoom to 115%.
- Replaces the inverted display-rectangle camera with a screen-coordinate camera whose positive Y direction points downward.

## Expected verification

### Native editor

1. Launch the native editor.
2. Place the pointer over Scene Map or Scene Rectangles.
3. Scroll one wheel notch.
4. Zoom should move gradually instead of jumping to a limit.
5. Stop scrolling; zoom must stop moving.
6. Scroll in the opposite direction; zoom must respond immediately and not reverse itself later.
7. Move the pointer over a dock or toolbar and scroll; the canvas must not zoom.
8. Press `F`; the active canvas should return to its framed default.

### Runtime

1. Launch the game.
2. Confirm the player, terrain, and map are upright.
3. Scroll in and out with the editor overlay closed.
4. Zoom should remain between 95% and 175% and stop when wheel input stops.
5. Press `Home`; zoom should smoothly return to 115%.
6. Confirm mouse-to-world interaction still resolves under the visible cursor.

## Validation

Passed in this environment:

- Repository architecture validation across 130 Rust files.
- Content validation across 182 JSON files.
- Complete registered editor/world/content validation suite through V66.
- Camera zoom/orientation regression guard.
- Asset-intake deterministic bake validation.

Unavailable in this environment:

- `cargo check --workspace --all-targets`
- Rust unit tests
- Clippy
- Rustfmt

Run on the normal Rust workstation:

```powershell
.\tools/build/Build.cmd validate
.\tools/build/Build.cmd check
.\tools/build/Build.cmd test
.\tools/build/Build.cmd editor
```
