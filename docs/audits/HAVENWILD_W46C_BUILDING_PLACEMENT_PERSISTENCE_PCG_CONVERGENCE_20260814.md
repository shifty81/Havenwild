# Havenwild W46C — Building Placement / Persistence / PCG Convergence

Date: 2026-08-14  
Pass: `167Z109W46C`  
Required baseline: green `167Z109W46B`

## Purpose

Carry W46B's native `BuildingInstance` runtime/editor materialization into stable authored placement, continuous/open-world placement, worldgen ingestion, save deltas, persistent door/opening state and a transport-neutral multiplayer replication contract without creating parallel building or visual authorities.

## Implemented

- Added authored / worldgen / player-built / diagnostic placement origin metadata.
- Added scene-local and continuous-surface placement spaces.
- Added stable global anchors for continuous-surface buildings.
- Split `building_instance.rs` into focused authoring, persistence and worldgen modules to remain below the project 750-line module ceiling.
- Added editor place/move/delete with stable IDs and immediate source persistence.
- Added save delta overlay with upserts, tombstones and per-opening persistent state.
- Added effective door/opening state shared by render, collision and interaction.
- Added deterministic worldgen BuildingInstance ingestion through the existing registry.
- Added global host building-state sequence separate from per-instance revision.
- Added transport-neutral host snapshot and replica apply semantics that exclude camera-local cutaway/floor-view state.
- Added `pcg_w46c_acceptance_0_0` with zero baked structure carriers.
- Added root utility command `46` / build command `building-persistence`.

## Baseline-safety correction

During implementation, five older-baseline files were initially touched even though they were not carried by the W46B overwrite archive. Those changes were removed before packaging. W46C does **not** overwrite:

- `crates/haven_save/src/lib.rs`;
- `crates/haven_net/src/lib.rs`;
- `crates/haven_authoring/src/command_bus.rs`;
- `apps/haven_editor_native/src/app/production_tools.rs`;
- `apps/haven_editor_native/src/app/editor_menu.rs`.

Instead, save-sidecar location is derived from the canonical save root in the exact W46B game path, editor authoring uses the existing `SceneMutation` command lane and exact W46B `input.rs`, and network semantics are transport-neutral until the listen-server transport is connected.

## Static/source verification

PASS:

- W46A BuildingRecipe authority;
- W46B BuildingInstance runtime/editor authority;
- W46C BuildingInstance placement/save/PCG convergence;
- development layout;
- architecture — 420 Rust files checked;
- project content;
- content integrity — 18/18;
- dedicated `building-persistence` build/fixture regeneration;
- new Python builder/validator syntax.

Rust/Cargo compilation and Windows graphical/runtime inspection are not claimable in this packaging environment because Cargo/rustc and Windows PowerShell are unavailable.

## Acceptance

Run locally:

```text
2. Build all
9. Validate current source
46. Build building placement + persistence authority
```

Inspect:

```text
pcg_w46c_acceptance_0_0
building_instance_acceptance
```

The next architecture pass after a green local W46C gate is W47 Interior Grammar / Furnishing Authority on the same BuildingInstance representation.
