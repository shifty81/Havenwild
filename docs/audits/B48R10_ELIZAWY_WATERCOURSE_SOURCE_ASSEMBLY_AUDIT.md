# B48R10: executable source-only summer assembly and scoped cliff/water audit

## Baseline / lineage
- User reported B48R9 Full Quality Gate GREEN and Commit + Push PASS on experimental lane. This handoff has **not** been built or PCC-gated in Windows.
- PCC update is an overwrite-safe **cumulative B48R7–B48R10 mapping overlay**, not a full source rollup and NOT cumulative from B22: those older complete PCC patch bytes were not provided here.
- Repackages B48R7, B48R8, and B48R9 payload source files byte-for-byte, with no deletions and no different bytes for any predecessor file.
- All new R10 paths are additive. The earlier B48R8 hydration and source-blob proof remain intact.

## New executable source proof
- `tools/automation/assets/Build-ElizaWySummerWatercourseEvidenceB48R10.py` takes the original `Terrain.zip`, `_ Test Scenes.zip`, and `4-season_terrain (1).zip` via `--archives`; output path via `--output`. It FAILS CLOSED for altered archives using five exact SHA-256 image hashes.
- 768×832 unscaled source-exact summer scene uses **887 recorded original source crops**, an independent pixel replay, repeated deterministic rebuild, PNG verification and a machine-readable placement ledger.
- Explicit watercourse topology 2 → 1 → 0, two source waterfalls (south demo row 1, rows 2/3, splash row4), 64px visible water core, one-tile *provisional* rock face behind upper pond entrance, existing W14 straight south cliff roles; source-original comparison is marked reference only.
- Indexed all 42 split-sheet waterfall-transition cells with exact source crop hashes, **not** per-cell gameplay role certifications. The distinct 192×224 split sheet is shown as an original source panel, not automatically tiled over the watercourse.
- New cliff-role review board isolates the W14 left-angle, straight, right-angle column components. These are not certified standalone exposed cliff ends.

## What is visibly still wrong / blocked
- Pond's stepped shoulders still need proper authored concave shoreline and water-to-cliff connectors; the temporary shoreline nine-slice is **NOT** production-approved.
- Top waterfall lip's cliff contacts and side framing do not yet match the original demo; no arbitrary visual scaling, generated pixels, rotation or mirroring is authorized.
- Pond 1-level face is an exception as low-relief basin *visual*, not a general permission for 1-level standalone true cliffs. Resolve structural ownership before game cutover.
- Bottom impact's correct submerged cliff face/rock transition, terminal tapers, passage opening and all 42 split-transition source roles remain unapproved.
- No runtime/editor/PCG renderer is connected to this R10 fixture. No claims about physical collision, animation parity, any season except summer, or Windows build.

## Prior contract & avoiding regressions
- Preserve `content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json` W14 source roles and 15-mask structural shape system. Do not replace them with a parallel heightmap or collision engine.
- Preserve B43 winter board approval only within its reviewed scope. North row0 of waterfall stays a **candidate**, not runtime-enabled.
- Do not promote recovered split-sheet 42 cells into a universal lip recipe merely because their coordinates and bytes are now known.

## Run offline source preview (when archives are available)
`python tools/automation/assets/Build-ElizaWySummerWatercourseEvidenceB48R10.py --archives <folder-containing-three-original-zips> --output <scratch-output-folder>`

## Next milestone
Match waterfall entrance and outlet edge colors/geometry against artist demo, resolve inward/outward corner pairs using original source layout, certify exposed cliff ends and 1-tile basin ownership, then implement a single existing structural/W14-derived recipe in BOTH editor and game and run full PCC gate.
