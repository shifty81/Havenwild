# Havenwild Terrain Tuple Brush Alignment Audit — Pass 167Z65

## Finding

The yellow cursor box and semantic paint coordinate were cell-aligned. The authored V7 tuple renderer sampled four semantic cells at `(x,y)`, `(x+1,y)`, `(x,y+1)`, and `(x+1,y+1)` but drew the resulting intersection graphic at `(x,y)`. That placed the intersection half a tile above and left of its geometric center.

## Corrective model

- Base terrain: pure owner material at integer cell origin.
- Mixed tuple: exact authored atlas cell at integer sample origin plus `0.5` tile on X and Y.
- Draw order: all bases first, all mixed tuples second.
- Shared implementation: one origin constant exported by `haven_world` and consumed by runtime and native editor.

## Evidence fixture

For one sand semantic cell surrounded by grass, the four exact V7 mixed tuple cells now meet at the center of the selected 1×1 cell. The former output met at the selected cell's upper-left corner.

## Exclusions

- No half-tile subtraction.
- No cursor-coordinate falsification.
- No generated transition artwork.
- No copied ElizaWy pixels inside the V7 lane.
- No cleanup/promotion of the historical Farmstead scene.
