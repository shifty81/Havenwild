# Havenwild W56IJ3 — Direct Editor/Client Visual Acceptance Parity

Status: **source-ready; local Rust build/test pending**

Baseline: `167Z109W56IJ2R1`

## Purpose

W56's dense integrated visual acceptance scene now has explicit isolated launch paths for both production-facing render consumers:

- **Client:** `Run -> Run W56 visual acceptance - client`
- **Native editor:** `Run -> Open W56 visual acceptance - native editor`

Both launch the same `worldgen_w56_integrated_visual_acceptance_v0_1` pack and the same
`w56_integrated_visual_acceptance` scene.

The editor acceptance path bypasses the normal saved development world so a stale save, selected scene,
or development-world descriptor cannot contaminate the comparison. It fails closed if the diagnostic pack
or scene cannot be loaded.

This does not add a new top-level Control Center choice and does not modify production worldgen.

## Acceptance

1. Run the Full quality gate.
2. Launch the W56 acceptance client and capture the board.
3. Launch the W56 acceptance native editor and capture the same board.
4. Compare cliffs 1–4, cottage, cave mouth, natural-object anchors/variants, water/path transitions, and object placement.

