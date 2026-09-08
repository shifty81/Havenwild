# Havenwild Global Surface Grid Audit — Pass 167Z79

## Root cause matrix

| Surface subsystem | Before Z79 | Z79 authority |
|---|---|---|
| Camera | Global | Global |
| Player exterior position | Local position + active chunk origin | Preserved |
| Terrain frame | Active map plus separate neighbor pass | One global visible tile window |
| V7 tuple neighborhood | One `TavernMap` only | Global cross-partition sampler |
| F3 Ground picking | Active-local and bounds-clipped | Global tile address |
| F3 Ground brush | Active map only | Multi-partition stroke |
| Outdoor explicit transitions | Inert | Inert |
| Object/NPC/zone/elevation editing | Active partition | Deferred to later global lanes |
| Minimap | Active partition | Deferred global map replacement |

## Certification targets

1. Stand within one brush radius of a horizontal or vertical storage boundary.
2. Paint a continuous strip across the boundary without crossing it as the player.
3. Verify both partitions change and one undo reverts the complete stroke.
4. Paint Grass beside Sand, Water and OceanDeep across the boundary.
5. Verify V7 owner fills and tuple overlays remain continuous without a one-tile line.
6. Walk across and back several times. Terrain must not pop, duplicate the active map or expose a grass fallback rectangle.
7. Confirm interiors, caves and ruins still use explicit scene transitions.
