# Havenwild W45C3A — Exact Roof Review Evidence

**Pass:** Pass167Z109W45C3A  
**Date:** 2026-08-14  
**Baseline:** Pass167Z109W45C2

## Purpose

W45C3A closes the evidence gap between the packageable Havenwild source and the intentionally machine-local pinned ElizaWy/LPC source mount. Roof source sheets are large authored topology atlases; the source rollup contains their catalog/provenance but intentionally omits the raw LPC repository. Therefore exact roof topology regions may not be invented from catalog dimensions alone.

## Implemented

- `content/buildings/roof_exact_region_review_contract_v1.json` locks exact source evidence and human visual review as mandatory before roof publication.
- `Build-ExactRoofReviewEvidenceV1.py` consumes the pinned LPC commit already mounted by Havenwild's dependency system and generates machine-local evidence for all seven roof source families.
- Every 32x32 address receives a pixel hash, alpha occupancy, local occupied bounds, edge-contact mask and exact source rectangle.
- Pixel-identical cell groups and alpha-edge-connected groups are emitted as review aids only; neither mechanism is allowed to assign semantic roof roles automatically.
- A coordinate-labelled 2x board is generated for every source sheet.
- A `roof_selection_template_v1.json` contains every role from `roof_topology_contract_v1.json`, but all selections remain empty until visually reviewed.
- The entire evidence folder is packed into `WORKSPACE/generated/structure_review/Havenwild_W45C3A_ExactRoofEvidence.zip` for upload/review.
- Root command 41 / `tools\build\Build.cmd structure-roof-review` first ensures the pinned LPC dependency, then requires all seven sheets and builds/validates the evidence bundle.

## Non-goals

W45C3A publishes **zero** roof visuals. The current 11/98 reviewed Structure source-sheet count remains unchanged. This is intentional. W45C3B may mark roof source regions reviewed only after the labelled evidence is inspected and accepted.

## Acceptance

Source validation passes without requiring machine-local evidence. When the pinned LPC mount exists, the evidence manifest is additionally checked for commit consistency and non-empty source sheets. The generated evidence ZIP is not runtime or package authority.
