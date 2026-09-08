# Havenwild Live Autotile and Terrain Transitions — Pass 51

## Purpose

Pass 51 replaces the editor's previous visual edge-blend approximation with a shared, data-driven live autotile resolver. Roads, floors, water, walls, cliffs, and cave walls now resolve from neighboring authored tiles while terrain-family transitions render from the existing Havenwild transition-rule system.

The authored tile grid remains the source of truth. Resolved shapes and transition overlays are derived data held in a per-scene cache.

## Supported autotile groups

- Road: Road, Stone Path, Mountain Path, Bridge
- Wood Floor: Wood Floor, Plank Floor
- Stone Floor: Stone Floor, Brick Floor
- Water: Water, Shallow Water, Deep Water
- Wall
- Cliff
- Cave Wall

## Dirty-neighbor recalculation

`LiveAutotileCache` observes the canonical tile and manual-override value for every cell. On first use it resolves the entire scene. Later edits mark only the edited cell and its one-cell neighborhood dirty. A single changed tile therefore recalculates at most the surrounding 3×3 region.

This synchronization path catches all editor changes, including paint strokes, rectangle/fill/replace operations, clipboard edits, undo/redo, scene reload, and imported content, without requiring every command implementation to maintain a separate render cache.

## Canvas controls

The Scene Map has a dedicated second toolbar row:

- **Auto: On/Off** toggles resolved autotile and terrain-transition previews.
- **Dirty: On/Off** displays the cells recalculated by the latest synchronization.
- **< / >** cycles the 16 manual adjacency presets.
- **Set Override** applies the selected mask to the cursor cell.
- **Auto Cell** removes the manual override and returns the cell to automatic resolution.

Keyboard equivalents:

- `P`: toggle preview
- `M`: cycle manual preset
- `O`: set override
- `Shift+O`: clear override

Manual overrides only apply to tiles that belong to an autotile group. They are highlighted with a magenta inset border.

## Terrain-transition preview

The cache also resolves Havenwild terrain-family edge and corner transitions. The editor renders previews for wet sand, foam, shallow-water edges, sand/grass/dirt blends, road/stone shoulders, and rock shadows using the same world-side rule resolver used by runtime-facing systems.

## Persistence

Manual overrides are stored in the existing line-save format as:

```text
autotile_override <x> <y> <group> <mask>
```

Older saves with no override records remain readable. Project scene duplication carries overrides with the scene, and rename/delete operations continue to use the project scene registry.

## Undo and redo

Override edits use the typed `SetAutotileOverride` operation. Repeated edits to the same cell coalesce inside a transaction, and undo/redo restores the exact previous optional override rather than serializing the full world.

## Validation

The editor reports:

- out-of-bounds override cells;
- duplicate overrides on one cell;
- override group mismatches after a source tile changes;
- invalid diagonal masks whose cardinal support is missing.

The Pass 51 contract is stored at:

`content/editor/autotile/live_autotile_authoring_contract_v0_1.json`
