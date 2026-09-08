# Terrain Autotile Pixel Studio Workflow — Pass167Z87

## Purpose

Pixel Studio becomes the repair and publishing surface for terrain families that do not yet have complete tiling information. It must not edit mounted ElizaWy, Universal LPC, or OpenGameArt source files in place. Every repair begins from copied reference layers and publishes a new Havenwild-owned normalized atlas plus metadata and attribution.

## Workflow

1. **Open a repair item**
   - Select the problem cell in Scene Editor or F3.
   - Terrain Tuple Inspector records the semantic corner signature and whether resolution is Exact, Authored Bridge, or Unresolved.
   - Choose the corresponding item from `content/editor/terrain_shape_repair_queue_v0_1.json`.

2. **Create the working document**
   - Ground transition: 32×32 cells using the 16-corner tuple template.
   - Same-family assembly: 32×32 cells using the 47-tile blob template.
   - Cliff structure: multi-cell document using the structural cliff recipe template.
   - Grid, source rectangles, pivots, and transparent padding are locked in metadata.

3. **Use controlled layers**
   - `00_reference_a` — read-only source material A.
   - `01_reference_b` — read-only source material B.
   - `10_owner_fill` — complete quiet base tile.
   - `20_boundary_shape` — edge/corner pixels.
   - `30_shading_cleanup` — lighting and palette reconciliation.
   - `40_alpha_cleanup` — transparent-pixel and fringe cleanup.
   - `90_preview_only` — guides and diagnostics; excluded from publish.

4. **Build every required shape**
   - Never repair only the screenshot’s one corner.
   - Complete the selected template’s entire required mask set.
   - Derive shapes from compatible source pixels, preserving source palette and lighting direction.
   - No quadrant cropping from disconnected larger details.

5. **Preview before publishing**
   - Isolated patch.
   - Long horizontal and vertical boundaries.
   - Outer corners and inner corners.
   - One-tile necks and narrow strips.
   - T-junctions and four-way junctions.
   - Randomized 3×3 and 5×5 semantic maps.
   - Cross-partition seam preview.
   - Animated-water contact preview where applicable.

6. **Publish atomically**
   - Export the normalized atlas.
   - Export stable tuple/shape metadata.
   - Register source provenance and license obligations.
   - Add editor thumbnail and runtime binding.
   - Generate acceptance scenes and automated tuple tests.
   - Publish only when editor and runtime resolve the same stable asset IDs.

## Current repair queue

| Family | Current issue | Required system |
|---|---|---|
| Rock Ground | Complex edges leak square Rock_Dark owner fills | 16-corner tuple |
| Stone Path | Direct Dirt/Grass contacts are incomplete | 16-corner tuple |
| Gravel | Several contacts rely on proxy tuples | 16-corner tuple |
| Mud | Mixed exact/proxy coverage | 16-corner tuple |
| Mountain Path / highland shoulder | Needs complete Rock/Grass/Dirt/Path contacts | 16-corner tuple |
| Cave Floor | Cave assembly transitions incomplete | 16-corner tuple |
| Floors, walls, bridges | Same-family assemblies incomplete or unpromoted | 47-tile blob |
| ElizaWy cliffs | Indexed sheets have no runtime structural recipes | Structural cliff recipe |

## Cliff-specific rule

A mountain is not a flat patch of Rock Ground. Rock Ground is a horizontal surface material. A production mountain requires semantic elevation tiers and structural faces derived between those tiers. Cliff caps, faces, corners, ramps, cave mouths, waterfalls, ladders, and bridge sockets are authored multi-cell structures and are never ordinary 32×32 ground brushes.
