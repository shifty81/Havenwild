# Havenwild W54C — Exterior Exact-Source Evidence Only

Date: 2026-08-16  
Runtime baseline retained: Pass167Z109W54B  
Pass type: evidence-only / no Rust / no runtime publication

## Why this pass exists

W54B is still the mandatory Windows compile + screenshot boundary. The user asked to continue before supplying that build result, so W54C deliberately performs only source-evidence work that cannot change runtime behavior.

The remaining exterior risk is not lack of source material; it is lack of exact semantic proof for the wall/back/side/corner grammar needed to skin a complete BuildingInstance without inventing facings.

## What W54C adds

- a source-controlled exact exterior review contract;
- a machine-local evidence builder over the pinned LPC source mount;
- labelled 32×32 coordinate boards and per-cell evidence JSON;
- a human selection template for facade/topology roles;
- explicit reference-only handling for `Paneled House A`, `Brick House A`, and `Brick House B`;
- validation proving this pass does not alter W54A runtime bindings or silently promote north/east/west cottage facings;
- Control Center option 59 for building the evidence bundle locally.

## Priority source families

Walls:

- Drywall — existing reviewed baseline;
- Siding, Plain — priority exterior review;
- Painted Walls — priority exterior review;
- Grainy Plain Wall — priority exterior review;
- Brick Wall A/B — secondary exterior grammar candidates.

Openings:

- Ornamental Windows B — existing reviewed baseline;
- Ornamental Windows A and Stone Windows A — review candidates;
- 12 Panel Door A — existing reviewed baseline;
- 32×48 Doorframe A/B and 15 Panel Door A — review candidates.

Roof:

- Flat Shingle Roof A — reviewed baseline topology;
- Gable Shingle Roof A — reviewed authored-module evidence;
- Hipped Shingle Roof A, Roof Trim and Brick Chimney A — unresolved topology/attachment review.

## Hard rules retained

- whole-house reference sheets are never promoted as one placeable;
- front artwork may not be rotated or mirrored to fabricate a side/back facing;
- exact source rectangle + human semantic review are required before publication;
- machine-local pixel analysis is evidence only;
- W54C does not modify `PublishedWorldAssetRegistry`, BuildingRecipe runtime geometry, Estate generation, or the W54A cottage recipe.

## Next action

Windows still needs to run:

```text
2. Build all
58. Validate integrated visual checkpoint
54. Run integrated Estate visual test
```

Optionally, once the pinned LPC mount is present:

```text
59. Build exact exterior review evidence
```

The resulting ZIP is review input for a later exact-component publication pass after runtime screenshots confirm what the current W54B/W54A exterior actually needs.
