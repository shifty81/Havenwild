# Pass 91B — Client Camera Zoom and Atlas Test Hotfix

Date: 2026-07-12

## Fixes

- Updated the stale Pass 90 atlas-coordinate test from Y=274 to the Pass 91 complete-role atlas coordinate Y=410.
- Increased the client gameplay camera default from 1.15x to 1.35x.
- Added client-only `Alt + mouse wheel` camera zoom.
- Added bounded zoom range of 0.85x to 2.20x with multiplicative 1.12 steps.
- Preserved zoom across scene transitions and editor-overlay toggles for the running client session.
- Routed camera clamping, screen/world conversion, terrain culling, actor culling, and backdrop culling through the same per-client zoom value.
- Reserved Alt+wheel for camera zoom so it is not forwarded to present or future hotbar/tool wheel selection.
- Added camera zoom unit coverage and validator V99.

## Build

Run:

```bat
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

The first command verifies/regenerates the pinned LPC terrain output. The full build validates the LPC dependency, runs Rust formatting/check/Clippy/tests, project validators, and packages the client/editor.

## Deliberate boundary

This pass fixes the build blocker and client camera controls. It does not claim the remaining squared wet-sand/dry-sand and diagonal shoreline topology is complete. That requires the next dedicated eight-neighbor shoreline resolver pass using convex and concave LPC roles.
