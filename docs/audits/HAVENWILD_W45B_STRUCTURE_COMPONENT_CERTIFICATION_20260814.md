# Havenwild W45B — Blocker-First Exact Structural Component Authority

## Scope

W45B converts the first blocker-first LPC Structure sources from sheet-level candidates into exact `PublishedWorldAssetRegistry` component candidates. It intentionally does **not** certify the visuals automatically.

## Published candidate set

- `door_basic` upgraded to real `12 Panel Door A.png` provenance with seven deterministic state/cache frames.
- `stairs_short_step_gray` and `stairs_short_run_gray` from exact `Short Steps A.png` regions.
- `fence_plain_horizontal`, `fence_plain_vertical`, `fence_plain_post` from exact `Plain Fence A.png` cells.
- `sign_wall_sword`, `sign_wall_shield`, `sign_wall_potion`, `sign_wall_inn`, `sign_wall_pub` composed from exact `Sign Backgrounds A.png` + `Sign Icons A.png` layers.

The generic standing `Sign` remains fail-closed. Wall plaques are not allowed to masquerade as standing signboards.

## Authority changes

- Added reusable published structure metadata: connection family, topology role, facing, level delta, wall attachment surface and sockets.
- Native editor and runtime both resolve explicit scene refs first, then the designated primary published legacy adapter.
- `ObjectKind` remains compatibility/gameplay classification; it is not restored as visual identity authority.
- Generated structure atlas is cache-only; exact source provenance remains in catalog records.

## Acceptance fixture

`content/worldgen/scenes/world_asset_acceptance/structure_component_acceptance_scene_v1.json` is diagnostic-only and contains the real door plus all ten W45B structural component candidates. Local review must verify source semantics, anchor, footprint, collision, state transitions, sorting and connector/wall behavior before promotion to `certified`.

## Validation

- W43B/C/D: PASS
- W44A: PASS
- W45A progression-aware source inventory: PASS (5/98 exact source sheets reviewed)
- W45B exact structure component authority: PASS
- Architecture/source profile through W43D: PASS; W44A/W45A/W45B targeted gates: PASS
- Windows Rust compile for W45B: pending local toolchain gate

## Next

W45C reviews floors, walls, wall borders, windows and roofs. W45D follows with bridges, platforms, pillars and miscellaneous structural support, then W46 composes certified components into BuildingRecipe authority.
