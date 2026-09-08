# Pass 167Z6 Direct LPC Terrain Authority Audit

## Screenshot diagnosis

The previous client frame showed three overlapping failures:

- Generated owner-fill terrain tuples produced visibly square or staircase-shaped material regions.
- Multiple generated/procedural terrain paths could contribute to the same cell.
- The always-on top-left developer panel covered the production portrait/vitals area.

## Corrective authority decision

The original pinned LPC source sheet is now authoritative for natural ground and water. Generated atlases are caches/compatibility artifacts only and are bypassed when the source sheet is present.

## Normal-build contract

`tools/build/Build.cmd all` verifies/mounts the LPC dependency, verifies runtime character/object assets, validates the project, and builds/tests applications. It does not regenerate the mapped terrain replacement atlas or terrain evidence boards.

## Certification boundary

Static validation proves source paths, cell bounds, transition-block bounds, normal-build routing, and HUD isolation. Visual correctness and FPS must be certified in the Windows client because Rust compilation and graphics execution are unavailable in the patch environment.
