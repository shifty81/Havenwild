# HW-ASSET-MAPPING-STATUS-OVERLAY-28

This pass keeps Havenwild standalone and advances the Atlas Mapper from a sheet-card index toward a visible mapping coverage tool.

## Added

- Reads mapped-sheet records while building the left sheet stack.
- Shows mapped tile count and coverage percentage on sheet cards.
- Shows active-sheet coverage in the Asset Intake inspector.
- Draws green source-cell badges from saved mapped-sheet records plus the current draft pieces.
- Upgrades mapped-sheet record schema to `havenwild.atlas_mapper_mapped_sheet.v0_3`.
- Adds a status-overlay contract for later Ember mirroring.

## Meaning

A green check on a source cell means exact mapper metadata exists for that tile coordinate. It does not mean the tile is published into runtime. Runtime publication still needs terrain/group semantics, layer role, collision, sockets/adjacency, provenance, and validation.

## Next

The next pass should add Learn From Scene and generate-next-unmapped behavior so corrected scenes become durable sheet knowledge instead of one-off mapper projects.
