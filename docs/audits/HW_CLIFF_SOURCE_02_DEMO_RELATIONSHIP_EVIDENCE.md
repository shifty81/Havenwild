# HW-CLIFF-SOURCE-02 — Official Demo Relationship Evidence

This pass is **evidence only**. It changes no runtime renderer, worldgen, collision, or traversal code.

## Pinned source verification

- **summerCliff**: hash=True dimensions=True — `C:/Users/Shifty/Desktop/Havenwild-main/assets/source/licensed/lpc_revised/Terrain/cliff_summer.png`
- **summerDemo**: hash=True dimensions=True — `C:/Users/Shifty/Desktop/Havenwild-main/assets/source/licensed/lpc_revised/_ Test Scenes/DemoGame - 2 - Summer.png`
- **testLandscape**: hash=True dimensions=True — `C:/Users/Shifty/Desktop/Havenwild-main/assets/source/licensed/lpc_revised/_ Test Scenes/Test Landscape.png`

## Source-native evidence status

- c8 cells observed in official scenes: `none`
- c15 cells observed in official scenes: `none`
- side-entry state: **unresolved_no_high_confidence_demo_match**
- right-terminal state: **unresolved_no_high_confidence_demo_match**
- runtime certification allowed: **False**
- foreign ramp retirement allowed: **False**

## Method

1. Decode the original pinned PNGs with a standard-library-only decoder.
2. Use only fully opaque source pixels as stable evidence.
3. Find source-cell occurrences at arbitrary scene pixel offsets; no 32px scene-grid assumption.
4. Resolve high-confidence cell identities and preserve ambiguous matches separately.
5. Record observed N/E/S/W source-cell adjacency.
6. Extract connected demo components containing c8/c15 evidence.
7. Export 5×5 visual context crops under `artifacts/audits/elizawy_cliff_source02/`.

## Important

A demonstrated match is evidence of source usage, **not** automatic runtime certification.
SOURCE-03 may promote an assembly only after reviewing the exact observed neighborhood and any available Tiled/TSX relationship evidence.

## DemoGame - 2 - Summer.png

- matched source cells: 6
- resolved scene positions: 1
- ambiguous positions retained: 29
- target observations: 0
- connected target components: 0

## Test Landscape.png

- matched source cells: 2
- resolved scene positions: 26
- ambiguous positions retained: 20
- target observations: 0
- connected target components: 0
