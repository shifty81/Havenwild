# Pass112 LPC Tiled Corner Model Fix

Pass111 proved that `lpc-terrains-v7` is the right replacement source, but it only
exported mixed terrain tuples from `terrain-map-v7.tsx`. Runtime fills still came
from the older Havenwild terrain atlas, so mapped transitions were drawn over a
different source texture family. That caused square halos, grid-looking patches,
and grass/sand/water edges that worked in some shapes but failed in others.

Pass112 treats the Tiled terrain-map as one coherent runtime source:

- export pure corner tuples as well as mixed corner tuples;
- render pure grass, sand, dirt, shallow-water, water, and deep-water fills from
  the same mapped atlas as their transitions;
- sample mapped terrain through Tiled-style 2x2 corner tuples;
- mark mapped entries as pure or mixed;
- suppress legacy transition overlays only where a mixed mapped transition covers
  the cell.

`Validate-LpcMappedTerrainReplacementV122.py` now guards the pure fill tuples and
the mixed sand/grass tuple so this path cannot silently regress back to a
mixed-only atlas.
