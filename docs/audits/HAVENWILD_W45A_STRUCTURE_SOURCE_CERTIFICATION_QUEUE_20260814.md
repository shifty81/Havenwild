# Havenwild W45A — Structure Source Certification Queue

**Pass:** Pass167Z109W45A  
**Date:** 2026-08-14  
**Status:** Source/static validation PASS; exact visual component review requires the pinned LPC source mount/local editor runtime.

## Result

W45A converts the structural roadmap into a finite source-authority queue without creating a separate structural registry. The pinned LPC slice catalog contains exactly **98** `Structure/` source sheets, all inventoried and classified.

| Role | Sheets |
|---|---:|
| wall | 20 |
| floor | 16 |
| door | 13 |
| wall border/trim | 7 |
| window | 7 |
| roof | 7 |
| stairs | 6 |
| bridge | 5 |
| misc | 5 |
| fence | 3 |
| building reference | 3 |
| pillar | 2 |
| platform | 2 |
| sign | 2 |
| **Total** | **98** |

Generated authority files:

- `content/assets/lpc/structure_source_inventory_v1.json`
- `content/assets/lpc/structure_component_promotion_queue_v1.json`
- `content/assets/lpc/structure_component_certification_contract_v1.json`

The first promotion priorities are **door, stairs, fence, sign**, because those directly replace W43 fail-closed legacy structure/object bindings. Floors, walls, trim, windows and roofs follow, then bridges/platforms/pillars/misc. The three complete-building source sheets remain reference-only for W46 BuildingRecipe decomposition.

## Certification gate

A source sheet is not a component. W45 requires an exact source rectangle/stamp, stable semantic identity, anchor, footprint, collision, sorting/occlusion, topology/connection rules, and editor/runtime parity before promotion through `PublishedWorldAssetRegistry` as `structure_component` or `structural_connector`.

Forbidden shortcuts remain locked:

- ladder art as stairs;
- standing screen as sign;
- generic Door/Fence/Stairs ObjectKind atlas fallback as production authority;
- promoting a whole source sheet as one ordinary placeable;
- generated atlas identity replacing source provenance;
- complete building reference sheet treated as a BuildingRecipe without decomposition.

## Validation

`tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py`

Root command:

```text
tools\build\Build.cmd structure-sources
```

Project Control Center:

```text
37. Build structural source certification queue
```

## Next

W45B reviews exact connected cells/stamps from the pinned source sheets, starting with doors/stairs/fences/signs, and publishes only accepted components through the existing `PublishedWorldAssetRegistry`. No source rectangle is guessed while the source mount is absent.
