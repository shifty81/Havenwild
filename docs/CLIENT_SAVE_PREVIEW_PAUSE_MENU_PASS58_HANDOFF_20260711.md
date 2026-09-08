# Havenwild Client Save Preview and Pause Menu — Pass 58 Handoff

## Scope

This pass completes the first usable client lifecycle around the three gameplay save slots introduced in Pass 57. It does not add gameplay-slot ownership to the native editor and does not add terrain-detail generation before structural island approval.

## Generated save-slot preview

Each newly created gameplay slot now exports an image assembled from the actual generated scene-map tiles:

```text
WORKSPACE/saves/slot_N/worldgen/previews/archipelago.png
```

The exporter is implemented in `crates/haven_world/src/world_preview.rs` so preview generation follows the same scene rectangle manifest, generated scene IDs, tile maps, and seeded archipelago positions used by the runtime world.

The preview currently visualizes the structural pass only:

- deep water
- water and shallow water
- wet sand and sand
- grass landmass interiors
- any future structural tile categories already present in the generated maps

It does not fake island silhouettes in the client UI.

## Main-menu save cards

Occupied save cards now show:

- generated archipelago preview
- save display name
- world seed
- island count
- exterior scene-cell count
- total scene count
- generation version

Older Pass 57 slot metadata remains readable because newly added metadata fields use Serde defaults.

## Pause and return-to-menu flow

Pressing `Esc` during gameplay freezes simulation and opens a client pause menu with:

- Resume
- Save Game
- Save & Main Menu
- Save & Quit Desktop

Returning to the main menu:

1. saves the active slot,
2. drops the active runtime `Game`,
3. returns to the client frontend,
4. rescans all three slot directories,
5. reloads generated slot preview textures.

The runtime no longer requires restarting the executable to switch gameplay saves.

## Ownership boundary

The native editor still owns only project authoring data. It contains no `ClientSaveSlot`, `slot_1`, `slot_2`, `slot_3`, or direct gameplay-save path logic.

## Files added

- `crates/haven_world/src/world_preview.rs`
- `crates/haven_game/src/client_pause_menu.rs`
- `tools/automation/validation/checks/editor/Validate-ClientSavePreviewPauseMenuV75.py`
- this handoff

## Main files updated

- `Cargo.toml`
- `crates/haven_world/Cargo.toml`
- `crates/haven_world/src/lib.rs`
- `crates/haven_world/src/island_pcg.rs`
- `crates/haven_save/src/lib.rs`
- `crates/haven_game/src/client_save_generation.rs`
- `crates/haven_game/src/client_frontend.rs`
- `crates/haven_game/src/main.rs`
- `tools/automation/validation/validate.py`
- `README.md`

## Validation completed in the packaging environment

Passed:

- architecture validation across 143 Rust files
- content validation across 187 JSON files
- seeded archipelago spacing V73
- client save-slot ownership V74
- client save preview/pause menu V75
- island PCG path V70
- structural archipelago workspace V71
- island assembly/save/routes V72
- Bash syntax
- Python syntax for the new validator and registry
- complete content JSON parsing

Cargo, Rustc, Rustfmt, and Clippy are not installed in this packaging environment. The Windows Rust workstation remains authoritative for compilation and tests.

## Windows Git Bash verification

```bash
cd /c/Users/Shifty/Desktop/havenw
./tools/build/Build.sh all
```

Build only the client:

```bash
./tools/build/Build.sh client
```

Expected executable:

```text
Build/HavenwildClient/HavenwildClient.exe
```

## Next recommended pass

Keep the structural islands visually empty until the silhouettes are approved. The next world-authoring pass should add island approval/locking controls and diagnostics in World Routes, followed by a metadata-only mainland zoning overlay. Mountains, capital roads, rivers, forests, buildings, and resource placement should remain deferred until the approved structural profile is locked.
