# Havenwild Client Gameplay Save Slots — Pass 57 Handoff

## Scope correction

The three gameplay save slots belong exclusively to the Havenwild client. The native editor remains a project-authoring environment and does not own, create, load, or delete gameplay slots.

## Client startup flow

Launching the Havenwild client now opens a dedicated three-slot main menu before a world is loaded.

Each slot supports:

- New Game
- Play
- Delete
- Open Save Folder
- Numeric world-seed entry
- Random seed generation

The client scans exactly three isolated gameplay folders:

- `WORKSPACE/saves/slot_1`
- `WORKSPACE/saves/slot_2`
- `WORKSPACE/saves/slot_3`

## Per-slot data

Each slot stores its own:

- `slot.json` metadata
- `world.tworld`
- generated scene-rectangle manifest
- world-paint deltas
- world-paint material state
- world-paint render cache
- reserved world-generation preview directory

No slot reads or writes another slot's world or paint state.

## New-game generation

Creating a new slot:

1. Accepts a user-entered or randomized seed.
2. Generates the seeded archipelago layout.
3. Generates all ten structural island landmasses.
4. Builds 43 generated exterior scenes.
5. Retains the nine existing authored/interior scenes.
6. Saves a 52-scene gameplay world inside the selected slot.
7. Starts the player at the generated mainland harbor scene.

Deleting a slot removes only that selected slot. Partial data is cleaned up if generation fails.

## Runtime persistence

The active slot now owns:

- F5/F9 world save and load
- runtime editor persistence
- world-paint deltas
- world-paint materials
- render-cache state
- last-played metadata

The HUD reports the active slot number.

## Editor boundary

`haven_editor_native` contains no gameplay-slot ownership. It continues to edit project-level world-generation profiles, island layouts, authoring data, and approval state.

## Release packaging

`tools/build/Build.sh` no longer copies development save contents into packaged applications. Packaged clients begin with an empty gameplay-save root.

## Validation completed

Passed in the packaging environment:

- Architecture validation across 141 Rust files
- Content validation across 187 JSON files
- Open-world preset validation
- Seeded archipelago spacing V73
- Client save-slot ownership and isolation V74
- Bash syntax validation
- Individual camera, island-PCG, Scene Bank, structural archipelago, island assembly, and Bash-entrypoint validators

The combined validator reaches the known slow asset-validation tail before the environment timeout. Cargo, Rustc, Rustfmt, and Clippy are unavailable in this environment, so the Windows workstation remains the authoritative compile/test environment.

## Windows Git Bash verification

From the repository root:

```bash
./tools/build/Build.sh all
```

Build only the client:

```bash
./tools/build/Build.sh client
```

Expected packaged executable:

```text
Build/HavenwildClient/HavenwildClient.exe
```

## Recommended next pass

After compile verification, the next client-facing pass should add generated slot preview cards, return-to-main-menu support, and slot-aware archipelago/world metadata display without moving slot ownership into the editor.
