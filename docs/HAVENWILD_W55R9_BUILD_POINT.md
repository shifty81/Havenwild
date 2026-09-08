# Havenwild W55R9 — Modular Building + PCG Acceptance Build Point

## Implemented
- Canonical deterministic `BuildingGenerationRequest` in `haven_world`.
- PCG output converges directly on `haven_core::BuildingDefinition` / `BuildingLayout`.
- No generated-building runtime model was introduced.
- Seven canonical acceptance fixtures: cottage, residence, shop, workshop, tavern, inn, mixed-use.
- Every fixture deliberately proves exterior and interior dimensions are independent.
- Multi-floor fixtures generate generic interior stair transitions.
- Consolidated building validation now rejects transition anchors that reference missing floors.
- Acceptance tests materialize runtime scenes and verify generic enter/return behavior.

## Build gate
Run Control Center option 2 (Build all), then option 10 (Run tests).

## After green
Continue W55R9 with editor-facing acceptance/reporting and persistence/multi-instance proof, then W55R10 normalization/certification.
