# Pass 163H Gameplay Consumer Integration Audit

## Integrated
- Map/path consumers can query centralized movement cost.
- Placement consumers can query centralized building class.
- Traversal can explicitly permit shallow and/or deep water without changing terrain collision data.
- World Builder inspection exposes the same semantic gameplay profile used by runtime code.

## Remaining
- Route concrete NPC pathfinding implementation to `terrain_movement_cost_at` when introduced/located.
- Route final building foundation placement to `terrain_building_class_at`.
- Bind footstep audio assets to `FootstepSurface`.
- Add player equipment/skill capability source for water traversal.
