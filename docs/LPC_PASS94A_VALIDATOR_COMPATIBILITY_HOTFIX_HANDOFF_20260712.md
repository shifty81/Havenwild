# Havenwild Pass 94A — Validator Compatibility Hotfix

## Cause

Pass 94 intentionally restored authored grass-to-sand diagonal inner corners and moved the player HUD implementation from `runtime_draw.rs` into `runtime_hud.rs`.

The older V102 validator still required the removed suppression test name and still searched `runtime_draw.rs` for the hotbar implementation. This made `tools/build/Build.cmd all` fail before Cargo compilation even though the Pass 94 source matched the newer V106 topology contract.

## Change

`tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py` now:

- requires `diagonal_grass_sand_contact_uses_authored_inner_corner`;
- requires `single_sand_cell_resolves_complete_eight_neighbor_ring`;
- continues requiring authored LPC adjacent-edge and water-bank tests;
- forbids the obsolete `diagonal_only_grass_sand_contact_does_not_emit_a_tail` test;
- validates the gameplay hotbar in `runtime_hud.rs`, where Pass 94 moved it.

No Rust, terrain atlas, topology, save, editor, or runtime behavior changed.

## Apply and verify

Extract the overlay into the repository root, then run:

```bat
tools/build/Build.cmd all
```

The V102 stage should report:

```text
LPC client/editor stability V102 validation passed
```

The build should then continue into Cargo formatting, checking, Clippy, tests, validation, and packaging.
