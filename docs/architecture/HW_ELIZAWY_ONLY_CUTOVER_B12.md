# HW-ELIZAWY-ONLY-B12 — source preflight and safe cutover boundary

**Status:** implemented audit/preflight; runtime cutover NOT implemented or certified.

## Decision

Use the pinned `ElizaWy/LPC` repository as the *candidate sole production visual provider*, including individually credited original authors and authorized derivatives. Preserve all other LPC, V7, OGA, and Universal LPC sources unchanged and reference-only **after** a governed cutover. Existing saves and scenes must remain loadable without silent asset-ID or terrain remapping. Do not alter PCC, ForgeGUI, engine, or Play From Here for this milestone. No substitute or generated artwork is approved by absence of source art.

This patch **does not** switch the active source family. The current V7-enabled client/editor remains as before so that a missing external source cannot create a broken production world. `content/assets/intake/elizawy_only_cutover_candidate_b12.json` is a deliberately inactive candidate, not an alternative asset registry or runtime configuration.

## Verified blockers from September 17 source rollup and remote B06

- Active terrain config is V7, while ElizaWy mainland is mapped only in part; don't flip JSON without a renderer/editor migration.
- Existing quality-gate scripts explicitly demand V7 and would fail a metadata-only change.
- The client/editor directly load the V7 terrain, a non-ElizaWy grass ramp, and Universal LPC character sources at some call sites. The B12 script enumerates the surviving source markers (it is a conservative dependency scan, not a proof of rendered pixels).
- The licensed source mount is not included in the full-source rollup; 64,365 catalog records alone do not certify physical files.
- The historical index declares one unreadable image. Identify and review it before whole-repository approval.
- GitHub `experimental` at audit time: `d970e65472187307a3cf21bbcaae8ac3644845d1` (B06). Later B07–B11 work was not verified in the remote checkout. Reconcile any pending local updates before modifying shared runtime files.

## Current usable foundation — KEEP

- `content/assets/intake/lpc_source_lock_v0_1.json`: pinned provenance and source files.
- `content/assets/lpc/lpc_project_asset_authority_v0_1.json`: domain routing, credits and stable IDs.
- `content/worldgen/elizawy_tile_lane_isolation_contract_v0_1.json`: pure ElizaWy terrain lane.
- `tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py`: full source audit/catalog builder.
- `tools/automation/assets/Audit-LpcOgaSourceCoverageA01.py`: offline licensed mount and discovery check.
- Existing world/cliff/character/PCC services remain untouched; no competing system is added.

## Execute on the actual Windows development checkout

From the `experimental` branch after reconciliation:

```powershell
py -3 tools/automation/validation/checks/assets/Test-ElizaWyOnlyCutoverB12.py
py -3 tools/automation/assets/Audit-ElizaWyOnlyCutoverB12.py --root . --report artifacts/audits/elizawy-cutover-b12.json
```

The preflight intentionally exits `2` and reports BLOCKED while the source is missing, V7 is active, or old provider references remain. This is expected and **does not mean the existing game is broken**. For an explicit full-source verification, add `--full-index`; it hashes every indexed source file and never modifies the originals. Without `--report`, output is stdout-only; with `--report`, only the selected report is written. It never imports, downloads, activates, modifies sources/saves or changes the PCC.

## Cutover sequence after preflight

1. Reconcile current experimental state and pending patches; record Git SHA and a backup. Keep Main protected.
2. Restore/verify the pinned original repository under its declared licensed mount, including per-folder credits. Run the existing A01 coverage tool and V167Z38 builder **only when ready to intentionally regenerate derived catalogs**.
3. Finish the ElizaWy-only ground/coast/water and structural cliff mappings using exact authored cells and complete assemblies; certify ladder/climbable-face traversal. Do not call visual tapering a ramp without evidence.
4. Update the game, editor, character workflow and quality-gate assertions as one compatible migration. Keep old providers for explicit legacy read-only compatibility, not ordinary new authoring.
5. Create one visual showcase: grass, sand, shoreline, seasonal water, rocks/cliffs/crest/endpoints, climbable faces/ladders, vegetation, building+interior, character+animation. Compare editor and game, save/reopen, measure frame performance. No visual approval based on a GREEN compile.
6. Only after actual approvals change the candidate activation and the active family. Subsequent packs require separate asset-level review, not automatic mixing.

## What constitutes progress

B12 supplies an executable dependency/source preflight and tests. It does **not** supply new licensed assets, claim the 64k files certified, rebuild the runtime, or promise that missing ElizaWy categories are magically present. Use the resulting blocker report to target the next source-compatible code batch without repeating the architecture rewrite.
