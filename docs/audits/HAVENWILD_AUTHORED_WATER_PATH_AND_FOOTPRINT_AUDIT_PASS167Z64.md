# Havenwild Authored Water, Path, and Footprint Audit — Pass167Z64

## Screenshot findings

### Deep to shallow water

The visible stair-stepped lake boundary was not caused by missing water art. The pinned ElizaWy summer terrain sheet already contains complete outer and inner shallow/deep cells. Runtime was cropping/combining portions and could also receive semantic masks that no single authored cell represents.

**Disposition:** remove water quadrant synthesis, draw complete source cells, and normalize unsupported semantic combinations.

### Mountain Path next to Sand

The visible block combines V7 `Dirt_Roots` and the Sand family. The exact V7 tuple catalog contains no direct pair, while `Dirt_Tan` has authored relationships with both.

**Disposition:** preserve Mountain Path as `Dirt_Roots`, but convert its immediate shore-contact cell to Road/`Dirt_Tan` as a style-local transition shoulder.

### Oversized F3 prop markers

F3 placement preview used generic or stale footprints rather than the deterministic authored variant selected by rendering. This was especially visible for one-tile bushes/plants and differently sized boulder components.

**Disposition:** resolve visual and collision footprints by stable object-atlas ID, selected from the same x/y deterministic variant function used by the renderer. Migrate old built-in natural objects on generation version 9.

## Authored water cell inventory

| Role | Source cells |
|---|---|
| Outer NW/N/NE | `(0,23)`, `(1,23)`, `(2,23)` |
| Outer W/fill/E | `(0,24)`, `(1,24)`, `(2,24)` |
| Outer SW/S/SE | `(0,25)`, `(1,25)`, `(2,25)` |
| Inner SE/SW | `(3,23)`, `(4,23)` |
| Inner NE/NW | `(3,24)`, `(4,24)` |

Coordinates are zero-based 32×32 cells in `Terrain/terrain_summer.png`.

## Non-goals

- No water image was generated.
- No tilesheet pixel was redrawn, recolored, or synthesized.
- No ElizaWy pixels were added to the isolated V7 atlas.
- No generic footprint was substituted for pack-defined custom objects.
- No final structural cliff recipe was claimed complete.

## Remaining visual certification

The Windows runtime still needs screenshots for:

1. Large lake/ocean shallow-depth contour after generation version 9 normalization.
2. Mountain Path approaching Sand with the V7 Road shoulder.
3. Each boulder variant with F3 visual/collision/interaction overlays enabled.
4. Bush, mushroom, herb, and tree preview bounds.
5. Existing save migration versus a newly generated world.
