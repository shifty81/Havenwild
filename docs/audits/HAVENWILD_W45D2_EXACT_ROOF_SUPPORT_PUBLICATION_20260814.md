# Havenwild W45C3B / W45D2 — Exact Roof + Structural Support Publication

Date: 2026-08-14  
Baseline lineage: `167Z109W40` cumulative overwrite

## Evidence consumed

The exact publication pass consumes the locally generated, pinned-LPC evidence bundles:

- `Havenwild_W45C3A_ExactRoofEvidence.zip`
- `Havenwild_W45D_ExactStructureSupportEvidence.zip`

The evidence is tied to ElizaWy/LPC commit `f07f7f5892e67c932c68f70bb04472f2c64e46bc`. Exact source SHA-256 values are retained in the publication manifests and validators.

## Published candidates

W45D2 adds 18 exact structural candidates: 11 roof candidates and 7 support candidates.

Roof: gray Flat Shingle field/edges/corners plus exact gray/brown Gable Shingle modules.

Support: Drawbridge leaf; Wood Bridge no-rails flat/arch/vertical modules; stepped dais; Stone pillar; Floral pillar.

All records remain `candidate`. Exact source identity is accepted; production visual/runtime/editor certification remains separate.

## Deferred by design

Hipped/adobe roofing, roof trim, chimney attachment grammar, rope bridges, bridge rail overlays, and Cement Platform A remain deferred. Their source sheets are not promoted by occupancy or whole-sheet heuristics.

## Authority rules

- Published exact source rectangles are immutable evidence-backed source regions.
- Generated atlases remain cache-only.
- Roof occlusion is camera-local presentation.
- Bridge rails are not walkable-deck collision authority.
- Pillar collision is footprint-rooted.
- Diagnostic SceneMap compatibility carriers are temporary acceptance-fixture plumbing only; W46 structural layers replace them in building authority.

## Progress

Pinned LPC Structure sources: **98**. Exact-reviewed source sheets: **18/98**.

## Validation

`Validate-ExactStructureModulePublicationV1.py` checks exact IDs, source rectangles, evidence hashes, deferrals, pack binding, acceptance scene coverage, source-inventory progress, roof camera-local occlusion, bridge collision separation and pillar footprint collision.

Root command **43. Build exact roof + support publication acceptance** rebuilds and validates the fixture.
