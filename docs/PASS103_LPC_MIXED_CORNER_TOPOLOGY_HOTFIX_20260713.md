# Havenwild Pass 103 - LPC Mixed Corner Topology Hotfix

Pass 103 continues from Pass 102 / V116 lineage.

## Why

Editor-painted sand over grass still left square grass blocks at concave
notches, T-junctions, and cross intersections. These were visible when a cell
needed both:

- a cardinal outer edge transition, and
- an authored diagonal inner-corner transition.

The resolver only emitted inner-corner requests when both adjacent cardinal
neighbors were still the owner material. Mixed edge-plus-diagonal contacts were
therefore missing the inner-corner piece.

## Changed

- Mixed edge-plus-diagonal contacts now request the LPC inner-corner role when
  either adjacent cardinal remains the owner material.
- Existing full outer-corner behavior is preserved when both adjacent cardinals
  match the diagonal neighbor.
- Added Rust regression coverage for the resolver and atlas request path.
- Added V116 static validation and wired it into `tools/build/Build.sh all` and
  `tools/automation/validation/validate.py`.

## Expected visual result

Sand/grass T-junctions, crosses, holes, and stepped notches should stop leaving
square grass blocks at the tile intersections.
