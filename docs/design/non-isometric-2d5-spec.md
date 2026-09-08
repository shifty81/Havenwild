# Non-Isometric 2.5D Rendering Spec

## Goal

Give the game a **2.5D look without using isometric projection**.

The target is a cozy, readable, top-down / 3-quarter presentation where:

- terrain still edits on a normal grid
- the camera remains easy to author against
- height reads visually through layers, shadows, cliffs, backdrops, and occlusion
- the result feels deeper than flat top-down without becoming a true isometric game

## Recommended Core Approach

### Use an Orthographic Base

The best implementation path is:

1. keep the gameplay grid orthographic
2. keep input and world editing in plain X/Y tile space
3. fake depth through render rules rather than changing the simulation grid

This is better than isometric for the current project because:

- the existing scene editor, tile brush, and map generation already assume normal grid coordinates
- y-sorting and height bands are already partially implemented
- world generation and save data stay simple

## Visual Depth Stack

Depth should come from five systems working together:

1. **height field**  
   per-cell elevation already exists and should remain the source of terrain tiers
2. **terrain bands**  
   shores, shallow water, deep water, cliffs, mountain rock, and highland paths should be derived from height thresholds
3. **y-sorted actors and props**  
   characters/objects sort by foot position, not sprite top
4. **front occluders**  
   trees, roofs, awnings, cliff lips, and tall decor need front/always-front style layers
5. **backdrop/parallax silhouettes**  
   distant mountain or forest masses create depth beyond the playable grid

## Camera Recommendation

### V1

- use a standard orthographic top-down camera
- keep the camera centered near the player
- smooth the camera target with interpolation
- do not rotate the simulation grid

### V2

Introduce a subtle **camera pitch illusion** rather than true perspective:

- vertically bias backdrop rendering upward
- draw cliff faces and raised edges with visible front faces/shadows
- use taller sprite proportions for walls, trees, signs, buildings, and props

### V3

Optional mild **oblique cheat**:

- keep logic in orthographic tile space
- allow a small render-only vertical offset for higher terrain bands and tall props
- do not convert to full cavalier/cabinet projection unless the whole art pipeline is rebuilt for it

## World Generation Rules For 2.5D

Generation should not only choose biome tiles; it should choose **readable depth composition**:

- low values -> deep/shallow water
- shoreline band -> wet sand / sand / pebble shore
- mid values -> grass / tall grass / paths
- upper band -> cliffs / mountain paths / mountain rock
- scene edge maxima -> backdrop candidates

Each generated scene should also expose:

- `playable_height_min/max`
- `backdrop_ridge_candidates`
- `occluder_spawn_candidates`
- `cliff_face_edges`

## Layer Model

Recommended render layer vocabulary:

```text
1. Backdrop
2. Ground
3. Ground Detail
4. Height Edge / Cliff Face
5. Object Base
6. Actor
7. Front Occluder
8. Always Front / FX
```

This keeps the game non-isometric while still delivering walk-behind and height-read cues.

## Sprite / Tile Art Guidance

- terrain remains tile-based
- cliffs need both **top surface** and **front face** treatment
- tall objects need a clear **foot point** for sorting
- tree canopies, awnings, rafters, and roof edges should be authored as front occluders where appropriate
- shadows should be stylized and directional, not physically simulated

## Best Fit For This Repo

For the current codebase, the strongest path is:

1. keep the current orthographic grid
2. expand the height system into explicit cliff-face and raised-edge rendering
3. add front-occluder support to the scene/layer model
4. keep y-sorting by feet/base pivot
5. use backdrop/parallax rendering for distant mountain and forest depth

This gives a convincing 2.5D result without throwing away the existing editor, save format, and terrain generation work.
