# Havenwild World Canvas Island PCG + Harbor Routes — Pass 54A

## Scope

This pass turns Scene Rectangles into a practical world-authoring surface and fixes the missing packaged client output.

## Scene Rectangles right-click workflow

Right-click an overworld scene cell to open a context menu with:

- Open assigned scene
- Assign selected scene
- Clear assignment
- Generate this scene
- Generate this island
- Generate all islands
- Frame this island
- Refresh harbor route

The context menu is drawn above all editor docks and closes after an action or an outside click.

## Procedural island generation

`haven_world::island_pcg` now generates one continuous semantic island across every Scene Rectangle belonging to a landmass.

The generator creates:

- deep water outside the island;
- shallow-water and sand/wet-sand coastline bands;
- grass and tall-grass interior terrain;
- a substantial central mountain using Cliff and Mountain Rock tiles;
- deterministic tree and ore-node scattering;
- a southern harbor scene with stone apron, road, and dock tiles;
- ordinary project-owned SceneMaps for every generated rectangle;
- coordinate-preserving one-cell transitions along every compatible walkable adjacent border.

The mainland generation is intentionally large: the current manifest supplies twenty editable mainland scene cells. Smaller configured islands use their own complete landmass generation.

Generated scenes are not flattened into one permanent texture or inaccessible PCG result. Each scene is inserted into the normal scene registry and can be opened in Scene Map, painted, populated, inspected, and saved like any hand-authored scene.

## Harbor and Region Graph integration

The existing main harbor node becomes the travel hub when the mainland is generated.

Every generated secondary island receives an Island Harbor region node. A Sea Route link connects that island harbor to the main harbor. Generating all islands builds the complete harbor travel overview automatically.

Harbor graph routes are reconstructed from saved scene assignments when the native editor reloads.

## Persistence

The native editor now loads and saves the same editable world document used by the runtime:

```text
WORKSPACE/saves/world.tworld
```

- `S` saves project metadata, Scene Rectangle assignments, and the complete world.
- `L` reloads all three and restores generated harbor routes.

This makes procedural island generation and subsequent per-scene edits persistent rather than session-only.

## Packaged applications

The build orchestrators now provide explicit application builds:

```powershell
.\tools/build/Build.cmd client
.\tools/build/Build.cmd apps
.\tools/build/Build.cmd all
```

Git Bash equivalents:

```bash
./tools/build/Build.sh client
./tools/build/Build.sh apps
./tools/build/Build.sh all
```

Outputs:

```text
Build/HavenwildClient/HavenwildClient.exe
Build/HavenwildEditor/HavenwildEditor.exe
```

The packaged folders also receive `assets/`, `content/`, and `WORKSPACE/saves/`, so the copied executables retain their runtime data instead of being isolated bare EXEs.

## Verification performed in this environment

Passed:

- Complete registered validation suite through V67
- Architecture validation across 133 Rust files
- Content validation across 183 canonical JSON files
- Tree-sitter structural parsing of all Rust files
- Python syntax validation
- JSON and TOML parsing
- Web JavaScript syntax checks
- Diff whitespace validation
- ZIP integrity validation

Cargo, Rustc, Rustfmt, and Clippy are not installed in this environment. Run the following on the Windows Rust workstation:

```powershell
cargo fmt --all
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
.\tools/build/Build.cmd apps
```

## Manual editor QA

1. Open Scene Rectangles.
2. Right-click a mainland cell.
3. Choose **Generate this island**.
4. Confirm the island fills many scene cells and the mountain occupies a substantial central area.
5. Right-click a generated cell and choose **Open assigned scene**.
6. Edit terrain or place objects in Scene Map.
7. Press `S`, close the editor, reopen it, and verify the edits remain.
8. Generate one or more secondary islands.
9. Open Region Graph and verify their harbor nodes connect to Main Harbor with sea routes.
10. Run `tools/build/Build.cmd apps` and verify both packaged executables exist and launch from their packaged folders.
