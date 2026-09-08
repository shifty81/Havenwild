# H20S Structural Elevation Normalization

Status: implementation milestone for Pass167Z109W81R30R44H7.

## Canonical grammar

Havenwild currently has one production cliff grammar:

- Level 0: ordinary traversable ground.
- Level 1: reserved for certified authored ramp transition cells only.
- Level 2+: true structural plateau/cliff terrain.
- Standalone one-level cliff walls are invalid production topology until the Level-2 system is certified stable.
- Small/thin legacy Level-1 regions become low-relief Level 0 terrain. They are traversed around rather than given ladders.
- Broad legacy Level-1 regions migrate to Level 2 so substantial raised land is retained.
- Legacy/AUTO `MountainRock` migrates to explicit Level 2.

## Ramp authority

The LPC directional ramp is a complete six-cell semantic corridor and a 3x4 visual stamp. Storage partitions do not own its topology. The canonical corridor levels are:

`2, 2, 2, 1, 1, 0`

This creates the two one-level transitions required to traverse the overall `2 -> 1 -> 0` descent. Level 1 is legal only inside a certified complete MountainPath corridor. Ramp footprints are cached during structural rebuild; render code never searches the neighborhood recursively per frame.

## Connector policy

- Constructed ladders require a true 2+ level drop.
- A one-level difference is not a ladder host.
- A constructed ladder may not terminate in swimmable water.
- Water-facing true cliffs reserve the natural vine/climb lane where access is intended.
- Stairs, ramps, ladders, vines, bridges, cave mouths, and waterfalls are explicit connectors/features. Artwork never invents traversal.

Natural vine artwork remains a separate visual asset task; until that asset lane is certified, water-facing ladder placement fails closed rather than substituting the wrong connector.

## Shared authority chain

`world settings/seed -> geographic surface -> hydrology -> structural normalization -> structural bake -> connector cache -> collision/traversal -> renderer -> editor/map`

The map is a semantic LOD of production geography. Explored/live cells overlay exact `SurfaceTerrainRecipe` data. It is not an independent hand-painted preview authority.

## Runtime migration

Before each active structural bake, loaded surface partitions are normalized together in global coordinates. This permits cross-partition ramp certification and prevents chunk boundaries from becoming topology boundaries. Only structural-level metadata is mirrored back into the live scenes; terrain, objects, hydrology, and authored visual overrides are untouched.

## Editor rules

Generic structural authoring exposes `0, 2, 3, 4`. Level 1 is not an ordinary brush value. Raise/lower operations step `0 -> 2 -> 3 -> 4` and reverse `4 -> 3 -> 2 -> 0`. The certified ramp planner owns Level-1 transition cells.

## H20S certification invariants

- geographic authority never emits standalone Level 1;
- streamed surface generation never emits standalone Level-1 cliff cells;
- thin one-high legacy shelves collapse to relief;
- broad one-high legacy regions promote to Level 2;
- AUTO MountainRock promotes to Level 2;
- complete ramp is exact `2,2,2,1,1,0`;
- complete ramp can cross a storage partition boundary;
- generic authoring cannot paint standalone Level 1;
- one-level forced ladders fail closed;
- 2+ dry cliffs may host constructed ladders;
- 2+ water-facing cliffs reserve natural vine access;
- renderer suppresses malformed one-segment cliffs outside a certified ramp;
- runtime, editor, and map use the same signed global coordinate frame.

## Acceptance world

The permanent structural acceptance fixture should contain straight and corner Level-2 cliffs, both ramp directions, cross-partition ramps, inland constructed ladder/stairs, water-facing natural-vine host, waterfall, cave mouth, low-relief route-around terrain, and map/editor/runtime coordinate parity checks.
