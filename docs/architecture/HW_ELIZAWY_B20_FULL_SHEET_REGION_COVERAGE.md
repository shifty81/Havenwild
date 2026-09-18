# B20 — Full-sheet canonical source regions (one shared seasonal geometry)

**Authority:** `content/worldgen/elizawy_ground_regions_b20.json` is a *region segmentation overlay* on the existing B19 canonical 16×26 coordinate map. B19 owns all 416 source-cell identities and all 2,080 seasonal source references. B20 does **not** create another asset provider, atlas, renderer, validator framework, per-season copy of the map, or incompatible source contract.

## Why this pass exists

B19 fully catalogued source-cell addresses but tagged only 35 of the 416 positions with provisional candidate-group membership. The B19 file did not establish whether the remaining cells are empty, details, portions of water gradients, shores, or repeatable terrain. That led to misleading "381 unmapped" messaging. B20 reconciles the **entire sheet** at the coarser, defensible *visual source region* level and distinctly marks true transparent source slots. It does not turn a region label into gameplay semantics.

The original summer sheet was examined with an exact 32px coordinate grid. B20 defines 47 source regions covering each canonical coordinate exactly once, including 3 transparent-only areas and other incomplete/partially transparent motifs. The region definitions are authored **once**; the master source-cell IDs and rectangle coordinates are reused unchanged for spring, summer, autumn, winter and winter-ice. Two winter-ice occupied-cell exceptions already identified in B19 stay attached to their canonical cells.

The builder refuses missing/overlapping regions; false "blank" tags; regions that claim artwork but are entirely blank; changed source PNG hashes; seasonal source-coordinate drift; B19 semantic, topology or runtime promotion; and regression of previously corrected water-detail classifications.

## Source meaning versus runtime meaning

* `sourceRegionId` groups source artwork for review. It is not a paint or gameplay semantic ID.
* `sourceRole=TRANSPARENT_SOURCE_SLOT` is transparent in **summer**. Seasonal exceptions must be handled explicitly; winter-ice may add artwork at the two B19 exception addresses.
* `sourceRole=VISUAL_REGION_ONLY` is a source-art cell that has not been approved as a repeatable tile, terrain corner, water interior, cliff, detail brush, or other runtime role.
* B16–B18's water-surface/dark-water *visual* candidates remain classified as pattern/gradient references, **not** water fill or depth evidence.
* All output approval flags stay false. B20 neither replaces the V7 renderer nor changes the editor, world saves, source PNGs, or PCC. Do not call the art production certified on a GREEN build alone.
* The 47 zones provide a single audit/view and future review targets. They do **not** establish 47 separate terrain materials or 47 automatic nine-slice compositions.

## Execute from the repository root

```powershell
py -3 tools/automation/assets/Build-ElizaWyGroundRegionsB20.py --root .
start WORKSPACE/generated/lpc/elizawy_ground_region_review_b20.html
py -3 tools/automation/validation/checks/assets/Test-ElizaWyGroundRegionsB20.py
```

Expected status: `CANONICAL_SOURCE_REGIONS_COVERED_SEMANTICS_UNAPPROVED`, 416/416 source slots, 47 regions, 305 source cells containing summer pixels, 111 transparent-only summer cells, 2,080 seasonal source references, no blockers. These counts derive from the B19 master and the original hashed PNGs and are not paintable-tile counts.

## Next coding step

Use **B19 + B20 as the only canonical geometry** to implement an ElizaWy *review scene / editor preview adapter* through the existing Havenwild asset-ID system. Start with exact authored source rectangles and verified standalone background, underlay, and overlay ordering. For expandable regions, add explicitly authored corner/edge/interior mapping and compare seams in a real editor/client scene, rather than assuming all 3×3 blocks are nine-slice-ready. Only after verified source-native combinations, provenance, terrain semantics, and gameplay are approved should the active runtime switch. Preserve V7 compatibility solely for older scenes and never silently borrow V7 artwork for new ElizaWy content.
