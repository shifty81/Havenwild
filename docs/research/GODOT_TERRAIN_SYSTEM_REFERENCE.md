# Godot Terrain System Reference — Pass 147R

## Authoritative reference scope

This audit uses the official Godot Engine stable documentation as the behavioral reference. Havenwild will not copy Godot source code. It will adopt the useful data-model concepts in an original Rust implementation.

Official references:

- https://docs.godotengine.org/en/stable/tutorials/2d/using_tilesets.html
- https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html
- https://docs.godotengine.org/en/stable/classes/class_tileset.html
- https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html
- https://docs.godotengine.org/en/stable/classes/class_tilesetsource.html

## Reference behavior

Godot separates a terrain set from a terrain inside that set. Terrain-set IDs and terrain IDs are independent. A tile can declare a center terrain plus terrain peering values around its sides/corners. The special terrain value `-1` represents empty space. The terrain mode determines whether matching uses corners and sides, corners only, or sides only.

Godot's terrain painter offers different connection intentions. Connect mode considers surrounding terrain on the layer. Path mode connects the supplied path cells and updates neighboring cells to create valid transitions. Manual selection remains available when automatic matching cannot express an authored exception.

Atlas-source identity is independent from terrain meaning. A tile source can be addressed by source ID, atlas coordinate, and alternative ID. This is the model Havenwild should use for stable authored-pattern identity.

## Havenwild translation

Havenwild should retain semantic `TileKind` values for gameplay/save state, but visual selection should use:

1. terrain set ID;
2. distinct terrain ID;
3. terrain matching mode;
4. complete eight-neighbor pattern signature where the mode requires it;
5. stable atlas source/coordinate/alternative identity;
6. deterministic candidate weighting;
7. explicit manual override identity;
8. structured trace when no exact candidate exists.

PCG and F3 editing must request patterns from the same resolver. PCG must not commit a route or material topology that has no valid authored candidate unless it also performs an explicit topology repair.
