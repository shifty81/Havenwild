# HW-TERRAIN-LANE-STANDALONE-MIRROR-26

This pass keeps the Asset Mapper standalone in Havenwild while locking the path for mirroring the generic editor/tooling pieces into Ember after green GitHub checkpoints.

## Runtime/editor decision

The terrain system is now described as a **Terrain Lane**, not a V7 lane. V7 remains a provider/fallback inside the lane. LPC Revised seasonal sheets become the intended canonical source-art profiles once mapped and validated. ElizaWy cliffs, LPC directional ramps, and waterfalls remain structural terrain providers.

## Standalone mapper behavior

The mapper now starts by indexing known Havenwild source sheet locations and showing them as sheet cards in the left panel. Selecting a card loads that sheet into the source preview. This is still lightweight: sheet cards are preloaded, but full image textures remain selected/on-demand rather than loading the entire asset library at startup.

## Left-panel upgrade

The left panel becomes an Asset Sheet Stack:

- sheet cards grouped by inferred family/provider
- mapped/unmapped status badges
- selected sheet source preview below the stack
- per-source-tile check badges for cells already used in the active mapping project

This is the first concrete standalone step toward the larger Asset Mapping Workspace.

## Ember mirror rule

Havenwild stays authoritative for this work until the standalone mapper lane is green. Ember should ingest the contracts and genericizable modules from GitHub later, not receive hand-copied divergent behavior.

## Still missing

The mapper still needs the real correction brain, family/topology group painting, pixel collision editor, source-sheet profile validator, and generated Havenwild world correction canvas. This pass provides the sheet-stack and authority foundation needed before those pieces can be implemented cleanly.
