# Havenwild Current Source Handoff — Pass167Z109W54F

**Authoritative continuation:** Pass167Z109W54F — Cottage Shell + Estate Crest + Cave Approach Repair.

## Why W54F exists

The first W54E runtime screenshots were trustworthy and rejected the W54E visual assembly: the two hipped-roof modules overlapped, facade strips projected into/above the roof, the cutaway interior still read as loose furniture on a floor plate, the south Estate Level-2 border had a fence/post band that looked like a duplicated cliff lip, and the good 1×2 cave mouth could not be entered from the player's walkable tile.

## W54F cottage

`havenwild.estate.starter_cottage` is now a **10×8** same-world BuildingInstance anchored at `[54,29]`.

- Rear room: **Bedroom** `[1,1,8,3]`.
- Front room: **Living / Crafting / Cooking** `[1,4,8,3]`.
- The rooms do not overlap.
- Internal doorway: `[5,4]`.
- Front doorway: `[5,7]`, therefore world tile `[59,36]`, still on the authored Estate route.
- Rear interior finish and the room-divider wall remain visible while roof/front facade cut away.
- North/east/west facing artwork remains fail-closed; collision remains authoritative.

The W54E twin hipped-roof use is retired from this cottage. W54F uses two already-reviewed exact brown gable modules. Their visual envelopes are edge-adjacent: west `x=0..4`, east `x=5..9`; there is no overlap and no gap. The south facade begins immediately below that roof envelope.

## Estate cliff-top repair

The decorative Estate boundary remains structural **Level 2**, but its plateau surface is now **Grass**, not a MountainRock top plate. Cliff faces remain elevation-derived. The old south fence/post band is removed from the Level-2 crest; any future gate must be a proper Level-0 assembly rather than decoration laid over the cliff edge.

## Cave

The cave mouth visual is deliberately unchanged: **1 tile wide × 2 levels tall**, with the exact 1×3 source evidence envelope retained.

- structural host: `[78,8]`, Level 2
- threshold/receiver: `[78,9]`, Level 0
- player interaction + scene transition: `[78,10]`, Level 0

This matches runtime transition semantics: the player triggers the scene transition from the tile they can actually stand on. A short Dirt apron at `x=78, y=9..11` makes the authored threshold receiver blend into the approach rather than a bright StonePath strip.

## Local gate

Apply the W54E→W54F patch, then run:

1. `2. Build all`
2. `62. Validate cottage + Estate visual repair`
3. `58. Validate integrated visual checkpoint`
4. `54. Run integrated Estate visual test`

Visual review should focus on the joined two-gable silhouette, two-room interior readability, grass-topped Level-2 cliff border, absence of the fence-band lip, and entering the unchanged 1×2 cave mouth from the clear approach tile.


## Pass167Z109W54G — cottage visibility/cutaway repair

The W54F screenshot proved the twin-gable roof geometry itself was no longer overlapping, but interior rear/divider wall art was leaking into the exterior because default-level wall rendering did not distinguish `building.wall_interior.*`. W54G fixes that runtime visibility boundary. The starter cottage remains 10x8 with Bedroom + Living/Crafting/Cooking. Outside, interior wall/opening groups are hidden. Inside, rear/divider walls use exact one-tile cutaway caps instead of three-tile drywall strips. Front and bedroom doors now default closed so they render as full doors until interacted with.

Local gate: `2. Build all` → `62. Validate cottage + Estate visual repair` → `54. Run integrated Estate visual test`.
