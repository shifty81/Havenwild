# H21A14AB49R2 — Door Hinge Test Contract Repair

The AB48 door correction intentionally retired the old per-frame horizontal compensation because the certified LPC 32x64 door cells already share a stable in-cell hinge. Runtime/catalog authority and the AB49 validator therefore require `draw_offset_px = [0,0]` for the static and animated `door_basic` frames.

The Windows Full Quality Gate after AB49R1 compiled successfully but stopped in `haven_assets` because two legacy W57 unit tests still asserted the retired `+12/-12` and intermediate `-1/-7/-12` offsets.

This repair updates those tests to verify the current stable-hinge contract instead of reintroducing the visual regression. It also strengthens the AB49 validator so legacy non-zero test expectations cannot silently return.

No runtime door artwork, frame order, timing, traversal timing, sounds, collision, or gameplay state transitions are changed by R2.
