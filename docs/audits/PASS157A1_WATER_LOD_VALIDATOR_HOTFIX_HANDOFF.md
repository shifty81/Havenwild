# Pass 157A1 — Water LOD Validator Hotfix

## Purpose
Pass 157A intentionally reduced water rendering from the historical 3/5-layer profiles to a calmer 1/2-layer bounded model. The legacy Pass 153D validator still required the removed `blend_layers: 3` and `blend_layers: 5` source tokens, so the build stopped before Cargo despite the runtime change being intentional.

## Change
Updated `tools/automation/validation/checks/terrain/Validate-WaterDetailLodPass153D.py` to validate the active 1/2-layer water-detail contract while preserving checks for:

- `WaterDetailProfile`
- bounded low-detail mode
- diagonal-corner suppression
- renderer consumption of `blend_layers`
- runtime camera/pressure budgeting
- V7 terrain authority diagnostics

## Runtime impact
None. This is a validator-alignment hotfix only.

## Verification required
Run the normal full Windows build. The capability-water stage should now report:

`Pass 153D OK: water blend cost is bounded to 1-2 layers by camera zoom while V7 topology remains authoritative`
