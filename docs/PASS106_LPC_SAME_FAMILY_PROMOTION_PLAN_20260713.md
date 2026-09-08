# Havenwild Pass 106 - LPC Same-Family Promotion Plan

Pass 106 continues from the corrected Pass 104/105 path.

## Purpose

The current grass/sand/water issues showed that runtime guessing is dangerous.
The right next step is to map authored LPC role coverage before enabling more
environment families in production paint.

Pass 106 does not change renderer behavior. It adds a source contract and
validator for the same-family tile families that should eventually autotile
against their own kind: roads, paths, bridges, caves, floors, walls, cliffs,
and modular building shells.

## Added

- `content/assets/lpc/lpc_same_family_promotion_plan_v0_1.json`
- `tools/automation/validation/checks/misc/Validate-LpcSameFamilyPromotionPlanV118.py`

## Promotion Order

Roads, paths, and bridges are the first same-family promotion target:

- `road`
- `stone_path`
- `mountain_path`
- `bridge`

After that, the plan promotes:

- cave floor and cave wall families;
- interior floors and walls;
- cliffs and mountain rock structure.

## Required Same-Family Roles

Before a family becomes production paint, it needs authored coverage for:

- center fill and isolated cells;
- four end caps;
- two straights;
- four corners;
- four T-junctions;
- cross intersections.

Mixed edge-plus-diagonal visuals remain deferred until a source family provides
authored cells for that exact topology.

## Safety

No layered complete replacement roles. A rendered cell may use one complete
replacement role at a time. This preserves the Pass 104 fix and prevents the
Pass 103 shoreline/sand regression where multiple full replacement cells were
stacked into one tile.

## Editor Policy

Same-family groups stay hidden or marked `Mapping Required` until their role
coverage is verified. Derived states such as foam, river mouths, crops, and
watered soil stay out of direct terrain paint. Props and vegetation remain
object/stamp placement.

## Next Implementation Pass

The next art pass should audit real source cells for `road_path_bridge`, build
preview boards for every required role, then generate a real same-family LPC
atlas from authored cells. Renderer selection should only be updated after the
source coverage is visible and validated.
