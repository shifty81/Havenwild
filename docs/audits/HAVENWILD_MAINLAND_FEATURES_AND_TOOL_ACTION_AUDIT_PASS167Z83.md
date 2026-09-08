# Havenwild Pass167Z83 Audit — Mainland Features and Tool Actions

## Source findings

- Pass167Z82 restored trees, bushes, herbs/flowers, reeds, and mushrooms, but its population report and generator contained no Boulder or OreNode path.
- The mainland generator created terrain and flora per storage partition but did not run a global road, capital, building-plot, or cave-host materialization pass.
- The Willowmere permanent-capital and service authority already existed and was retained.
- Gameplay tool-to-animation mappings already matched the LPC compatibility matrix.
- Player movement did not consult `player_action_remaining`; movement could therefore override the action presentation immediately after tool use.
- The ElizaWy repository audit and cliff role catalog identify exact seasonal cliff, wall, roof, door, bridge, and related structure source families, but raw external source files are deliberately not packaged in the current rollup.

## Z83 decisions

- Add one global-coordinate mainland feature pass rather than per-scene road scripts.
- Keep exterior scene rectangles as persistence/streaming partitions only.
- Build Willowmere streets and plot reservations from the existing capital contract; do not restore a mandatory player Farmstead.
- Use only existing ObjectKind and audited footprint/render paths for boulders, ore, civic props, and Cave Entrance.
- Preserve existing authored roads during save migration.
- Treat missing packaged ElizaWy building/cliff pixels as a promotion blocker, not permission to generate, recolor, crop, or mix replacement art.
- Make the action timer the exclusive movement lock and ignore repeated tool-use input until it completes.

## Remaining production lanes

1. Promote exact ElizaWy wall/roof/door/building families into packaged semantic stamp catalogs.
2. Materialize complete Willowmere buildings and interiors on the Z83 plot reservations.
3. Bind the audited seasonal cliff recipes to the height-derived structural cache renderer, collision edges, ramps, waterfalls, and cave mouths.
4. Create dedicated generated cave instances and route each promoted Cave Entrance to its own instance rather than the retained legacy cave placeholder.
5. Add city/property/business/world-map markers and filters after the physical sites are stable.
