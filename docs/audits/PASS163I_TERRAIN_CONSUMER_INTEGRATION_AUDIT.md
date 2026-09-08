# Pass 163I Terrain Consumer Integration Audit

## Integrated consumers

- Movement-cost query
- Farming-state query
- Footstep-surface query
- Fishability query
- Standard-building placement query
- Shallow/deep water traversal query
- Object collision-footprint placement

## Deliberately deferred

No concrete NPC pathfinder or terrain footstep audio playback system currently
exists in the audited source. This pass provides and tests the canonical
consumer APIs without inventing parallel placeholder systems.
