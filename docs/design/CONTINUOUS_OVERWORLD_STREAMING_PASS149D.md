# Pass 149D — Continuous Overworld Streaming

Pass 149D removes legacy exterior edge transfers from the active player path for the authored starter surface chunks.

## Runtime behavior

- Exterior movement uses local map coordinates only for rendering and collision.
- The active authored surface binding supplies the global chunk coordinate.
- Crossing a map edge resolves the adjacent authored chunk directly.
- The player keeps the matching local edge position instead of using a transition spawn.
- Exterior transition rectangles remain inert migration metadata.
- Interior, cave, mine, dungeon, and special-area portals remain explicit scene transitions.
- Character-world persistence stores global world-tile coordinates for exterior locations.

## Streaming windows

The runtime contract exposes a 3x3 active window and 5x5 preload metadata window. This pass resolves the authored starter chunks synchronously; background generation and asynchronous chunk residency remain the next expansion.

## Authored starter bindings

- Farmstead: 0,0
- North Road: 0,-1
- South Field: 0,1
- East Woods: 1,0

The inherited scene documents are retained as authored chunk payloads while their exterior transition semantics are retired.
