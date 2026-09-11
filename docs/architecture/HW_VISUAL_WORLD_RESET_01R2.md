# HW-VISUAL-WORLD-RESET-01R2

The first RESET-01 gate compiled after R1 and then correctly exposed another
historical assumption: editor tests still required neighboring deep water to be
changed to shallow water when painting a coastline cell.

The same audit also found a second presentation-driven semantic mutation:
`normalize_lpc_authored_material_contacts_region` changed `MountainPath` into
`Road` beside sand solely because the current V7 tuple catalog lacked that pair.

R2 retires that mutation centrally. The compatibility function remains callable
so older runtime/editor paths continue compiling, but it never changes map
semantics. Unsupported pairs remain discoverable through
`lpc_mapped_terrain_supports_tile_pair` and the existing audit/report paths.

Acceptance rule:

- exact paint changes only explicitly painted semantics;
- coastline paint changes only explicitly painted semantics;
- unsupported atlas/material contact is diagnostic, not a map rewrite;
- explicit Hydrology mode remains a separate semantic authoring operation and
  is not conflated with presentation compatibility.
