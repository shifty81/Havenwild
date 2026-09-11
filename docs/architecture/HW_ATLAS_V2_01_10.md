# Havenwild Atlas/Terrain V2 — Passes 01–10

Baseline: `f8b47a750d11ea894995854ded03d70b0885fd0a`  
Candidate block: `HW-ATLAS-V2-01-10`  
State: authority-foundation implementation complete; Full Quality Gate, exact-current consumer cutover and visual acceptance intentionally pending.

## Goal

Normalize the proven Havenwild terrain, transition, cliff and ramp systems around one source/atlas authority without rewriting gameplay semantics, rebaking worlds or inventing replacement artwork.

The target flow remains:

`Authored source -> canonical atlas catalog -> semantic/structural resolver -> shared draw recipe -> editor/runtime/PCG consumers`

`TileKind`, structural levels, collision, save state and persistent world identity remain gameplay authority. Provider identity and source-sheet coordinates are presentation metadata only.

## Baseline/rebase rule

The 2026-09-09 source rollup predates several current GitHub changes. Before packaging this block, every existing file selected for overwrite was compared against the exact `f8b47a7` authority. Files whose current GitHub blob differed from the rollup were deliberately not overwritten. Their remaining V2 consumer cutover is recorded in `content/architecture/terrain_atlas_v2_cutover_debt_v1.json` and must be rebased from exact-current source after this foundation passes the Windows gate.

This is intentional regression prevention, not an incomplete rollback to the older rollup.

## Pass record

### HW-ATLAS-V2-01 — Freeze and audit current authority

Locked `f8b47a7` as the input authority and established an exact-base overwrite rule for the overhaul. Existing V7, ElizaWy and LPC systems remain the source of truth; the new V2 layer catalogs them instead of synthesizing a replacement tileset. Current files that could not be proven identical to the supplied rollup are tracked as guarded cutover debt rather than overwritten.

### HW-ATLAS-V2-02 — Canonical atlas catalog

Added `content/assets/terrain_atlas_catalog_v2.json` and `haven_assets::terrain_atlas_catalog_v2`. Stable IDs describe production, compatibility and source-reference atlases with source path, publication path, manifest/role metadata, cell geometry, authority class and roles.

### HW-ATLAS-V2-03 — Raw source/slice authority

V7 direct source-cell lookup reads the existing audited `v7_terrain_role_catalog_v0_1.json`, preserving the complete 32×64 source grid while separately constraining legacy compatibility-transition blocks to the historically reviewed 16×26 region. LPC cliff/ramp roles now expose stable atlas identity while retaining their exact authored whole-cell and 3×4 stamp geometry. No crop, mirror, stretch or rotation path was introduced.

### HW-ATLAS-V2-04 — Semantic terrain resolver V2

Added `AuthoredSurfaceDrawPlanV2`, an atlas-facing visual plan layered on top of existing semantic terrain authority. It explicitly distinguishes exact tuple, owner-fill fallback and unmapped states. The existing `AuthoredSurfaceResolution` API now delegates to the V2 plan as a compatibility projection, so current exact-base runtime consumers can enter V2 without an all-at-once API migration.

### HW-ATLAS-V2-05 — Unified transition/Wang source authority foundation

Registered the reviewed direct V7 compatibility-transition source blocks in the canonical data catalog and validated their source bounds. Existing exact tuple/Wang/transition topology continues to own topology. The newer `terrain_transition_draw.rs` on `f8b47a7` was not overwritten from the older rollup; replacing its remaining renderer-local compatibility coordinate table with catalog lookup is a post-gate exact-current cutover item.

### HW-ATLAS-V2-06 — Structural atlas resolver foundation

Cataloged ElizaWy cliff/waterfall and LPC cliff-ramp source/publication identity alongside terrain atlases. The exact-current LPC ramp provider now exposes stable atlas identity without changing its certified multi-cell stamp geometry. The newer ElizaWy provider/render recipe files are left untouched in this block and remain authoritative for contour geometry.

### HW-ATLAS-V2-07 — Editor/runtime parity bridge

The exact-current runtime base-terrain cache already calls `resolve_authored_v7_surface_for_map`; that compatibility API now delegates to `AuthoredSurfaceDrawPlanV2`, giving the runtime retained-terrain path a safe V2 entry point. The current native editor still calls the lower-level mapped owner/transition APIs directly, but those APIs remain the same V7 semantic/source authority. Exact-current editor call-site conversion to the V2 record is deliberately deferred until after this foundation compiles and tests GREEN.

### HW-ATLAS-V2-08 — Proving-ground contract

Added `terrain_atlas_v2_proving_ground_v1.json`, binding existing terrain/cliff acceptance scenes into one V2 matrix covering pure materials, transitions, junctions, unsupported diagnostics, structural heights, corners, ramps, ladders, caves and waterfalls. It is diagnostic-only and not production-registered until the Full Quality Gate and paired editor/client visual acceptance succeed.

### HW-ATLAS-V2-09 — Rendering normalization guard

Added an explicit exact-baseline cutover-debt record for renderer/editor files that differ from the supplied rollup. The desired end state remains removal of duplicated renderer-local V7 material IDs and compatibility-transition coordinates, but this pass prevents a stale overwrite from erasing newer rendering/editor work. The next cutover must start from each recorded `f8b47a7` blob (or a verified descendant), not from the September 9 copy.

### HW-ATLAS-V2-10 — PCG/world reconciliation gate

Added `terrain_atlas_v2_reconciliation_v1.json`. No existing world/save is rebaked or migrated. PCG remains semantic. Reconciliation is blocked until the foundation is GREEN, the exact-current consumer cutover is complete, and editor/client proving-ground captures show parity. Persistent-world migration remains separately gated after that.

## Intentional non-changes

This block does **not** change `TileKind`, terrain collision, elevation semantics, structural levels, ramp/ladder movement rules, world seeds, persistent IDs, V7 source art, ElizaWy source art, LPC ramp pixels, source licenses/provenance, or existing world/save content.

It also does not claim that every current renderer/editor call site has already been migrated to the V2 record. Compatibility APIs remain on purpose until the Full Quality Gate verifies the new authority foundation.

## Next gate

Apply this overwrite-capable incremental patch to the clean `f8b47a7`-derived repository and run Havenwild's normal **FULL QUALITY GATE / CERTIFY GREEN**. If source/build/tests are GREEN, the next bounded pass is the exact-current renderer/editor consumer cutover recorded in `terrain_atlas_v2_cutover_debt_v1.json`, followed by the paired terrain/cliff proving-ground visual inspection before any production rebake or migration.
