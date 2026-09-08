# Havenwild Structural Archipelago Workspace — Pass 55 Handoff

## Purpose

Pass 55 turns the previous 43 exterior scene rectangles into 10 coherent editable island
landmasses and makes the native editor's World Routes and Overworld Layout work at the island
level. It deliberately stops before biome/detail generation so island silhouettes and scene-cell
assemblies can be approved first.

## Scene accounting

- 43 generated exterior scene cells
- 10 island landmasses
- 9 existing authored/interior scenes retained
- 52 expected world scenes after Generate Structural Archipelago

The generator replaces/rebuilds only the 43 exterior PCG scenes. It does not flatten or delete
the existing Scene Bank/interior content.

## Structural PCG

The active structural tiles are:

- deep water
- shallow water
- sand
- wet sand
- grass

The generator evaluates one global field across all scene cells belonging to an island. Shared
scene borders therefore continue the same coastline and land interior rather than producing one
mini-island per scene. An assembly-boundary mask adds coast against empty grid slots, allowing
non-rectangular scene-cell arrangements without raw grass edges.

Deferred until a later approved pass:

- central mainland mountain and mountain caves
- biome regions
- roads and town placement
- forests and vegetation
- resources and ore
- buildings and harbor dressing
- authored gameplay props

## Native editor workspaces

### World Routes

- Shows all 10 island landmasses as live assembled previews of their assigned editable scene maps.
- Island previews are selectable from either the map or the left island list.
- Harbor nodes and sea-route lines render over the archipelago.
- `Begin Route Here` stores the selected island as a source.
- Select another island and use `Connect Route to Selected` to create a custom ship route.
- Custom routes persist in `content/worldgen/harbor_routes_v0_1.json`.

### Overworld Layout

- Operates on the island selected in World Routes or the left island list.
- Displays only that island's scene-cell assembly.
- Scene cells resolve generated `ProjectSceneId` values, not only legacy `SceneId` templates.
- Move the selected scene cell with `Shift+Arrow`, inspector buttons, or right-click actions.
- Occupied grid positions are rejected.
- Moving a cell updates its grid position and archipelago preview placement.

### Scene Editor and Scene Bank

- Scene Editor remains the per-cell terrain/object/zone/transition authoring surface.
- Scene Bank remains the reusable interior/cave/dungeon/special-scene workspace.

## Menus and saving

The native editor now has visible File, Edit, View, and Help menus plus a permanent Save All
button.

Save All is available through:

- File > Save All
- top-right Save All button
- Ctrl+S
- F5

Save All writes:

1. project metadata
2. scene rectangle manifest
3. scene rectangle assignments
4. harbor route catalog
5. editable world save (`WORKSPACE/saves/world.tworld`)
6. ten assembled island PNG previews (`content/worldgen/island_previews/*.png`)
7. a complete route-overlaid archipelago PNG (`content/worldgen/island_previews/archipelago.png`)

## Build and validation

From Git Bash at the repository root:

```bash
./tools/build/Build.sh all
```

Generate only the structural preview PNGs:

```bash
./tools/build/Build.sh island-previews
```

Focused validation:

```bash
python tools/automation/validation/checks/worldgen/Validate-StructuralArchipelagoWorkspaceV71.py
python tools/automation/validation/checks/worldgen/Validate-IslandAssemblySaveRoutesV72.py
```

Static validation completed in the packaging environment:

- architecture validation
- content JSON validation
- open-world preset validation
- camera/runtime framing validation
- island-PCG/harbor validation
- Scene Bank validation
- Bash entrypoint validation
- island-PCG test-path validation
- structural archipelago validation
- island assembly/save/route validation
- deterministic generation of 10 preview PNGs

Cargo and Rustc were unavailable in the packaging environment. The Windows Rust workstation must
perform the final `cargo fmt`, workspace check, strict Clippy, tests, and application packaging
through `./tools/build/Build.sh all`.
