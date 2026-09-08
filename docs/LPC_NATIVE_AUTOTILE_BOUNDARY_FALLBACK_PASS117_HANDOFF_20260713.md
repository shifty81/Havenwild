# LPC Native Autotile Boundary Fallback Pass 117

## Root Cause

Several generated LPC transition-atlas compound masks are full neighbor-fill cells. That is valid as a generated placeholder, but it is not safe for runtime rendering when the player paints a small island, cutout, or one-cell water shape.

Examples:

- A single water cell surrounded by land can resolve to mask `0x0f`.
- A one-cell grass/dirt/sand cutout inside another material can resolve to mask `0x0f`.
- Opposing-edge and T-junction masks can also be generated as fill cells.

If those unsafe compound atlas cells are drawn directly, the renderer covers the placed tile center with the neighbor material. That produces disappearing one-cell water, square holes, mirrored corner chunks, and material bleed-through.

## Runtime Rule

The placed tile owns the center of its cell.

Runtime may draw authored atlas art for simple safe outer roles:

- single edges: `0x01`, `0x02`, `0x04`, `0x08`
- adjacent outer corners: `0x03`, `0x06`, `0x09`, `0x0c`

Runtime must not draw generated atlas entries for unsafe compound masks:

- opposite edges
- T-junctions
- enclosed four-sided cells

Those masks keep the base tile visible and draw procedural boundary edges instead.

## Water

Water must remain eligible for the live same-family autotile atlas. A one-cell water placement surrounded by land should render water plus shoreline boundaries, not disappear into land fill.

## Validation

`Validate-NativeAutotileBoundaryFallbackV124.py` locks the runtime guard:

- water is no longer filtered out of the live autotile base pass
- unsafe compound transition atlas masks fall back to runtime edge drawing
- the obsolete early return when a transition atlas exists is removed
