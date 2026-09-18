# B14 — ElizaWy-only NEW authoring: source-only routing, no runtime switch

## Actual changes
- Existing `lpc_project_asset_authority`, `lpc_project_foundation_authority`, `lpc_revised_category_coverage`, and project editor source-library contracts now prefer **only ElizaWy** for **new authoring**. Universal LPC and V7 remain recorded for reference and legacy save compatibility, not automatic artwork substitution.
- The existing ElizaWy library marks collection-wide runtime promotion **off** until records have **individual** approval. Its generated domain catalog builder now stamps provider identity, candidate state and explicit nonapproval on every record; zero-byte/invalid-header images are quarantined.
- B14 audits source policy, optional prior B13 full-index evidence, existing generated catalogs and quarantines, while refusing to infer that metadata changed the active engine or that source hashes amount to visual certification.

## Explicitly NOT done
- Active `content/worldgen/terrain_visual_family_authority_v0_1.json` remains V7. The old mixed renderer, character composer, V7-specific gate validators and existing saved worlds are not changed. A metadata-only V7 switch breaks runtime/render validation and is prohibited.
- This change makes canonical source **candidate catalog data** safe for new authoring; the currently running editor/client may still have legacy direct sources. Do not treat B14 GREEN as project-wide visual cutover, character animation approval or asset production approval.
- Per-asset licenses and credits require review; a full source inventory is not a redistribution license decision. The original 0-byte cardigan emote remains source-preserved but quarantined.

## Windows checkout steps (Experimental)
1. Root-drop this ZIP through the existing PCC and run the normal gate; do not extract or manually replace scripts.
2. Keep existing successful B13 full-index JSON in `WORKSPACE/generated/lpc/elizawy_b13_report.json` and the mounted pinned source. Run the **existing** catalog builder explicitly, which reindexes the 64k source files (expensive):

```powershell
py -3 tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py --force --strict
py -3 tools/automation/assets/Audit-ElizaWyCandidateRoutingB14.py --root . --require-local-evidence --report WORKSPACE/generated/lpc/elizawy_b14_routing.json
```

3. Inspect the B14 JSON. `SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED`, no blockers, `productionApproval:false`, `runtimeCutover:false` is the intended result. If the catalog builder fails, retain the existing GREEN source checkpoint; no manual provider flip.
4. Run `py -3 tools/automation/validation/checks/assets/Test-ElizaWyCandidateRoutingB14.py` for regression fixtures. Keep the original source backups until certification evidence is archived.

## Next actual cutover tasks
B15 source-map terrain and water exact cells; B16 cliff geometry and climbing assemblies; B17 waterfalls; B18 structures and objects; B19 player/NPC layers and animation. The actual runtime + native-editor shared switch, active-only validators, legacy world loads, screenshot parity, collision and performance must be committed together once mapping receipts exist. No V7 or ULPC pixel fallbacks on new production content.
