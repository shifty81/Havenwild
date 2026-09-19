# Havenwild B48R12 — single-patch reconciliation and source-only contact proof

## Baseline and safety
B48R9 is the user-reported GREEN/pushed experimental checkpoint. B48R10 and B48R11 were provided as two NOT-YET-APPLIED transports. Apply ONE consolidated B48R12 ZIP; do not apply either old transport before or after this one. This patch is a cumulative B48R7–B48R12 **mapping overlay**, not a complete source rollup or an equivalent of B22–B48R6 source bytes.

## Reconciliation
- All B48R7–B48R9 source/mapping payload files retained unchanged from the uploaded B48R10 cumulative transport.
- All three B48R11 payload files retained unchanged.
- B48R10 audit text, placement ledger and W14 component source board kept as HISTORICAL / REJECTED evidence; does not imply assembly approval.
- Rejected B48R10 candidate worldgen JSON, scene-builder script, two failed PNG previews and generated pyc files deliberately EXCLUDED from installable source overlay. Both original user-supplied ZIPs can be retained separately for byte-exact recovery. No installed path is deleted.
- All newly added files are additive. No renderer/editor/gameplay activation or physical height normalization change.

## New concrete source evidence
- Four pixel-exact cropped regions from the original artist's summer demo, with source-rect and RGBA pixel hashes, plus both complete original split cliff/water sheets on one review board. Source images not redesigned or regenerated.
- Full-cell matching probe across 42+42 source addresses returned zero directly matching *complete* 32x32 opaque masks in the artist demo. This is inconclusive about whether the sheets were used as alpha overlays, masked pieces, or alternate animation phases; it forbids claiming a direct whole-tile scene match.
- B48R12 validator fails closed if this audit is promoted to runtime, transparent addresses become placeable, B48R10 is treated as approved, source hashes/artist crop hashes change, or general level-1 cliffs are enabled. Includes explicit corruption/rejection tests.

## Remaining critical mapping order
CW01 and CW03 first: actual matching authored left/right waterfall shoulder and splash/rock-water toe; do not insert floating cliff strip. CW06/07 terminal/taper and corner grammar next; CW04 continuous recessed pond wall and water, then CW05 dedicated basin physical policy; only then a new whole source-exact scene and editor/client/PCG integration.

## Verification scope
This handoff can pass ZIP checksum/manifest, offline source identity and metadata checks. Windows build, PCC full gate, runtime rendering, nav, collision and visual scene approval are NOT claimed.
