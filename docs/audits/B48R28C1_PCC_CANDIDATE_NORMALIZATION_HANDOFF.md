# Havenwild B48R28C1 — project-owned PCC normalization of the Bevy candidate

## Exact source baseline

- GitHub `shifty81/Havenwild` / experimental HEAD `78ff838499015ff434dbd935ae5daf9cbd11a02e` B48R28B GREEN, verified before authoring.
- Existing `HavenwildPccHost.ps1` and `HavenwildTools.ps1` remain unchanged; latest source for `PccCommandExtensions.ps1` and `PccCommandHost.ps1` was byte-matched to GitHub blob SHA before surgery.
- ForgeGUI pinned SHA `eafa8e78efd54142a19e66d8be7b7d3985af23d2` remains unchanged. Bevy=0.19.0, bevy_egui=0.42.0.

## Implemented here

1. Added four exact keys in the preexisting `PccCommandExtensions.ps1` registry, surfaced in the normal Build/Run menus and provider command discovery.
2. Added narrowly whitelisted dispatch in existing `PccCommandHost.ps1`; candidate requests **do not** get forwarded to the legacy `HavenwildTools.ps1` registry, whose historical registry is different.
3. Added thin `HavenwildBevyCandidate.ps1` adapter, which delegates to Python candidate verifier/build/runner; no independent PCC, Git, patch intake, logger, or launcher.
4. Added fail-closed candidate gate: experimental branch; B48R28B ancestry; real root PCC; pinned dependencies; actual original ElizaWy source SHA + credits + source receipt; exact scene hash, dimensions and identity.
5. Candidate Cargo check/run uses the isolated candidate manifest; candidate Cargo.lock if present, otherwise prints an explicit reproducibility warning. No production Cargo graph or canonical saves are touched.
6. Tests cover branch, ancestry, tampering, stale fixture, exact provider registration, and safe forwarding; main branch operation is blocked.
7. Updated candidate architecture contract and README to reflect actual registered operations and unknown/uncertified stages.

## Why this is a bounded integration rather than the whole R28C feature pass

The Bevy candidate currently displays the verified original atlas, not an ElizaWy-certified resolved world. The old `AuthoredSurfaceDrawPlanV2` is V7-bound, and reusing it would violate the new ElizaWy-primary rule. We must first derive/publish source-exact ElizaWy recipes in the existing mapper/Asset Authority, then wire their shared draw plan into Bevy and current runtime/editor. Do not invent mappings, silently import V7 as ElizaWy, or label a semantic debug grid as an approved world render.

## Actual gates for the operator

- Apply this cumulative package through the root PCC on experimental, not main.
- Register and locate the four candidate commands through PCC/ForgePY provider; status without source is allowed, verify/build/run require staged originals and exact current receipt.
- Run Python test suite; then Windows Cargo check and run through PCC, inspect original source preview/Inspector docking, and run FULL QUALITY GATE. None of the Windows steps was executed by this authoring environment.
- Preserve B48R28B GREEN until PCC receipts pass. This is a cumulative B48R26–B48R28C1 patch, not a complete source rollup.

## Next pass — genuine shared world rendering, no duplicate mapper

Bind a source-exact certified ElizaWy recipe manifest (source hashes, source regions, footprint, collision and animation roles) from `apps/haven_atlas_mapper_lite` via Havenwild Asset Authority. Implement one shared draw-plan DTO with exact source coordinates and deterministic layer/order, adapter to Bevy sprites and current Macroquad runtime/editor shadow comparisons, then add actual scene picking/authoring transactions with revision checks. R28D is actual-game PIE; do not promise runtime parity until proven.
