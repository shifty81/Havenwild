# B48R11 — Havenwild ElizaWy cliff/water source-to-recipe gap audit

**Baseline:** B48R9 was reported GREEN and pushed by the user. B48R10's preview was rejected and is superseded for visual acceptance. This audit is additive and cannot certify or alter the existing renderer. Do not install the rejected B48R10 candidate as a prerequisite.

## Verified against supplied source files
- `Terrain/Mountain, Waterfall Transitions (Summer).png`: 192×224, SHA-256 `8deafc172a31e96409d31ef0e7c23eee1b25d3c903ff24f6ab602f56985c1ae4`; 6×7=42 grid addresses, **40 with pixel content and 2 entirely transparent** (`c4r6`, `c5r6`). The existing B48R8 42-entry source inventory counts addresses, not 42 independently useful sprites.
- Original `Terrain/Mountain, Animated Water (Summer).png`: 192×224, SHA-256 `0e0998191aedd8562b8d31342c443536765c7223561997d14d091553b93b7cfc`; a second sheet with cliff/rock-to-water visuals, which must be inspected together with the recovered transition sheet. The split sheet alone cannot provide a recessed rock wall around an entire pond.
- `Terrain/cliff_summer.png`: SHA-256 `94bd2ddb2c51677498453486092ef28e57e0c1880f4334359189229590298147`. W14 remains authoritative for ordinary south walls: west/straight/east `c1/c2/c3` × `r7 crest, r3 repeat body, r8 foot` with the host-level crest and exact N receiver rows. Historical c10r9–r11 generic wall mapping is retired.
- B48R10 ledger: **0** placements from the recovered transition sheet, **10** stand-alone basin wall-body cells; thus the new sheet was *displayed* but not used to solve any contact. The prior pixel-hash/deterministic test was insufficient to certify adjacency.

## Exact source-layout grouping, not yet an auto-tiling recipe
The 42 source addresses have been uniquely assigned to six intact visual neighborhoods for research (view `B48R11_CLIFF_WATER_SOURCE_ROLE_BOARD.png`):

| Group | Grid (col,row,width,height) | Status |
|---|---|---|
| Earth upper bank/water | (0,0,3,2) | Source layout only |
| Grass upper bank/water | (3,0,3,2) | Source layout only |
| Earth/water inset left | (0,2,2,5) | Source layout only |
| Central vegetated-to-earth inset | (2,2,2,5) | Source layout only |
| Grass/water inset right | (4,2,2,4) | Source layout only |
| Empty atlas addresses | (4,6,2,1) | Transparent, not placeable |

None of these arbitrary rectangular survey regions is independently approved as a game asset. Cell position and pixel equality do not demonstrate adjacent/diagonal join correctness. Establish exact natural authored assembly windows by matching the artist's demos and testing all contact edges.

## Prioritized unfinished cliff + water mapping

| Gate | What still requires source-role mapping | Required visual/functional proof |
|---|---|---|
| CW01 upper cliff-water source | 2-wide river banks, left/right waterfall shoulder, lip, neighboring exposed cliff ends | Both banks touch cliff opening with no blunt vertical cut or floating water |
| CW02 vertical connector | south mouth, repeat body, height formula; north candidate, east/west families, verified 2/3-column widths | One continuous drop at intended footprint, phase-locked animation; no blue rectangle |
| CW03 lower impact / submerged cliff | authored rock-to-water face, toe, splash backing, splash-front and water plane | Lower water touches rock and fall, no intervening grass or floating brown strip |
| CW04 full recessed pond | continuous straight side faces, north/south wall, all concave/convex shoreline corners, outlet | Water is contained by a connected cliff ring, including behind/adjacent to splash |
| CW05 structural height | structural 2+ cliffs versus proposed 1-tile basin visual face; renderer/physics ownership | Must not serialize arbitrary 1 as structural level (existing normalizer promotes it to 2) |
| CW06 cliff terminal grammar | c1/c2/c3 connected end rows, both tapered exterior returns, north-facing ends, side-facing returns | No abrupt freestanding last column; true walk-through where cliff *ends* |
| CW07 corner/mask topology | all 15 masks and actual concave turns (not isolated source cells); thin caps 7/11/13/14/15 normalized out in fresh PCG | Mask-specific corner/terminal, no invented mirror, half-crop or generic fallback |
| CW08 water-valley / side contact | authored `c9-c11 r0-r2` and `c12-c14 r0-r2` socket families plus animation-water sheet | Correct orientation and adjacency against the exact waterfall-direction artwork |
| CW09 functional attachments | narrow/wide cave mouths, vines, ladders, stairs/ramps/bridge interfaces at cliff ends | Collision, access and navigation agree; no accidental traversal through wall/fall |
| CW10 ecology + season + worldgen | shoreline type, depth, water connectivity, spring/autumn/winter/ice/frozen variants, deterministic recipe selection | Per-season source windows checked independently, consistent footprint and no broken random joins |

## Existing architecture to retain, not duplicate
- `TavernMap.structural_levels -> StructuralCellV2 -> CliffShape15` owns topology and collision; original artwork does **not** calculate world height.
- W14 source-role grammar owns current ordinary south cliff rows. W6 connected-recipe rule prohibits treating every 32×32 address as a world asset; W8 normalizes thin PCG contours and forbids inferred concave art.
- Editor/client should consume one typed recipe and the same world identity. A worldgen heightmap may propose structural levels, but existing `structural_elevation_normalization.rs` states level 1 is reserved for certified ramp corridors and normal editor input `1` normalizes to `2`. A 1-tile *appearance* at a recessed pond therefore needs an explicitly reviewed basin profile or approved normalization change, not an invented global one-level cliff exception.
- `runtime_structural_waterfall_draw.rs` still draws a full 96×160 south source envelope, 64×224 east/west, North disabled; it cannot yet use the B48R7 split-crest mapping. Review B48R10 visual acceptance separately from B48R9 source gate.

## Order of implementation and nonnegotiable acceptance
1. Reconstruct CW01+CW03 from original demo **in place**, paired with `Mountain, Animated Water` and recovered transitions. Create side-by-side left/right seam crops and prove proper rock/water contact before a new whole pond.
2. Certify CW06+CW07 cliff turns and terminals (ordinary contour plus exceptional cave/climb/waterfall openings). Do not reuse the invalid isolated horizontal face.
3. Resolve CW04 basin-specific renderer and collision/height treatment, then CW02 waterfall connector bodies and widths; require full adjacency + overlap/hole + hydrological continuity tests, not merely a source-crop ledger.
4. Only after a visually approved source-exact complete summer scene, implement one shared existing world/editor/client resolver; certify collision, navigation, seasonal swaps and deterministic seeded PCG. Windows Full PCC Gate then runs locally.

**Status:** source-window mapping and a concrete defect/gate ledger delivered; none of CW01–CW10 is newly marked gameplay-certified. No production switch, source edits or renderer mutation in this audit.
