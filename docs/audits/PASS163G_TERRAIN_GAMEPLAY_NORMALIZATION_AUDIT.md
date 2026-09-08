# Pass 163G Terrain Gameplay Normalization Audit

## Normalized

- 32 save-compatible terrain identities have gameplay profiles.
- Collision remains independent from tuple artwork and shaders.
- Shallow and deep water are distinguished semantically.
- Farming state distinguishes tillable, tilled, watered, crop-occupied, and
  greenhouse terrain.
- Building placement distinguishes allowed, foundation-required, and forbidden.
- Movement costs and footstep surfaces are centralized.

## Remaining integration work

1. Replace local pathfinding cost tables with the central profile.
2. Replace local farming checks with `FarmingClass`.
3. Replace local building checks with `BuildingClass`.
4. Route footsteps and terrain audio through `FootstepSurface`.
5. Surface gameplay profile details in the World Builder inspector.
6. Add runtime tests for water traversal abilities and bridge/foundation rules.
