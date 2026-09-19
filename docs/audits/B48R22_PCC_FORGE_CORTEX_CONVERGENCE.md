# B48R22 — Havenwild PCC / Forge / Cortex convergence checkpoint

## Baseline and authority

- User reports B48R20 was GREEN/committed/pushed. B48R21 is NOT certified: a browser-renamed ` (1).zip` was held by legacy intake *after* its name was registered as required, causing a false required FAILED ledger entry. Do not silently call this a failed application or clear it as APPLIED.
- B48R22 is cumulative from B48R7 through B48R21, but is not a complete source rollup. It supersedes B48R21; apply only one cumulative ZIP. Windows gate and GUI are not certified by this source-only package.
- The Havenwild project-owned PCC is the sole authority for root-drop intake, verification, rollback, Full Gate, Git GREEN and diagnostics. ForgePY/Forge GUI delegates to its provider. Cortex requests actions via the selected Forge project context; it does not create its own project-wide PCC, patch ledger or source-control writer.
- Existing `.forge/project.toml`, `tools/forge/HavenwildForgeAdapter.py` and `tools/forge/HavenwildPccProvider.py` already supply project adapter groundwork; do not overlay a duplicate PCC or put `project.control.json` in strict root without first reconciling BOTH root auditors. The new bridge is read-only and additive.

## Exact source changes

1. `tools/control/PccRootHandoffClassifier.ps1`: classify browser-renamed cumulative/incremental transports before the intake ledger. A single structurally valid `(1).zip` may be renamed to its canonical filename if no canonical transport exists, after checking supplied checksum sidecar. If the canonical name exists, hold the extra original without applying it and write a holding receipt with both hashes. Unrecognized/bad-checksum files remain visible and fail closed. No automatic update or ledger success claim.
2. `tools/control/HavenwildPccHost.ps1`: call this classifier BEFORE `Get-PccPendingPatchFiles`, preflight and `PENDING` registration. Retain PCC replacement restart, source fingerprint and existing transaction path.
3. `tools/control/ReconcileHeldDuplicatePatch.py`: exact B48R21-only local recovery. For the already falsely FAILED entry, require experimental lane, B48R20 receipt or a verified superseding B48R22 receipt, matching held source ZIP hash and exact manifest, absence of a root or applied B48R21 transport, and exact known failure text. Only then, with `--apply`, backup and change FAILED to DEFERRED/NOT APPLIED. It **does not** install B48R21, mark it APPLIED or certify anything. If the patch actually applied, this helper deliberately refuses and a distinct receipt-based reconciliation is required.
4. `tools/forge/HavenwildIntegrationBridge.py`: read-only JSON discovery descriptor for one Havenwild project context and stable existing PCC command keys, plus logs/artifact paths and truthful external-connection state. Does not claim Forge/Cortex process integration.
5. Regression checks for the bridge and held patch recovery. No changes to the game renderer, mapper content, ElizaWy source artwork or certified source mappings.

## The normalized user experience (target, not claimed implemented)

**Forge workstation** is the common GUI/PCC front end with project selector, Git/ForgeGit/Vault, activities, status, queued patches, and a persistent console. It locates and dispatches the selected project's internal PCC, displays stdout/stderr, status, receipt, and gate outcomes, and never owns a second Havenwild ledger. Opening the Havenwild project exposes the source tree, assets and current mapper scene. **Cortex** lives in that project's console/chat context and requests tools through Forge's permissioned operation broker; progress and evidence flow back to the same Activity surface. **ForgeGUI Core** is reusable desktop chrome/docking/panels, not another PCC. Havenwild's existing Macroquad standalone atlas mapper stays the single authoring authority until a tested GUI-host migration is complete.

The mapper's two equivalent inspection surfaces should load any activated Summer sheets on the left and use the right canvas for an editable source-exact scene. A future *true* reroll must use the exact same runtime/worldgen/elevation and Asset Authority recipes (including 0/+1..+30, proper cliff/water contacts and navigable connectors). Current `Stage missing` is **not** that reroll. One mapping receipt should bind original sheet hashes, role and adjacency maps, scene version, generator seed, manual corrections, review PNG and approval scope. Visual approval, technical source validation and runtime publication remain three separate states.

## Required follow-on implementation, in order

1. **PCC transport certification:** Windows run with original and `(1)` filenames, duplicate same/different hash, bad manifest/sidecar, valid applied receipt, staged/held state, restart, root audit, Full Gate and an automatic debug bundle on failure. Repair false legacy entries only with direct evidence.
2. **Forge provider takeover gate:** register Havenwild in the current ForgePY project catalog using the existing `.forge` adapter and compare its discovered command registry with this bridge; map `patch.apply`/recovery capability to real existing commands before granting Forge native patch delegation. Forge must preserve the root ZIP bytes and call the project PCC. Do not copy ForgePY's internal implementation into Havenwild.
3. **Cortex handoff:** prove selected Havenwild project identity in Chat, Workbench and Vault; permissioned operations, streaming logs, cancelled jobs, diagnostics; regression test no cross-project writes, no bypass of PCC approval, and consistency between CLI and GUI. This requires changes/test evidence in Forge and Cortex sources and cannot be certified by a Havenwild-only patch.
4. **GUI host decision:** inspect actual ForgeGUI Core consumer API, dependency compatibility and standalone mapper embedding. Prototype equal pane/inspector/docking without duplicating mapping data. No wholesale Macroquad-to-egui rewrite in the stability patch.
5. **Mapper/game parity:** implement shared cliff/water topology, preview height +1..+30, source-bound review/approval and real seeded reroll; tests include coastal level-one cliffs, recessed ponds and connected mountain routes. Preserve the prior winter review approval without extrapolation.

## Installation and verification

- Keep B48R20 as last certified checkpoint until a new Windows gate passes.
- If prior B48R21 `(1).zip` is a verified HELD transport with B48R20 still last-applied: after installing B48R22, run `py -3 tools/control/ReconcileHeldDuplicatePatch.py --root .` (dry-run), then append `--apply` only if all checks pass. This only clears the false block; it does not certify B48R22.
- If a canonical B48R21 was actually applied, do not use held-state recovery; inspect the applied receipt and hashes. If no exact held archive is available, stop and provide the debug bundle.
- Place one canonically named B48R22 ZIP in root, approve governed intake, require explicit `[PASS]` receipt, then Full Quality Gate and commit/push GREEN only after success. The new duplicate handling is only active after B48R22's PCC code is installed.
- Compile and exercise the CLI/mapper GUI on Windows; Linux Python unit checks in this package alone do not certify Windows PowerShell or actual Cortex/Forge integration.
