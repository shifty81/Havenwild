# Havenwild W55R9 Build Point

Pass target: `167Z109W55R9C`

This build point resumes from the W55R8I build/test-certified source and begins forward building-authority acceptance work.

## Included

- deterministic `BuildingGenerationRequest` in `haven_world`;
- PCG resolves directly to `haven_core::BuildingDefinition` / `BuildingLayout`;
- seven deliberately different acceptance requests;
- interiors remain independently sized and larger than the exterior fixtures;
- generic multi-floor stair transitions;
- runtime entry/materialization/exact-return acceptance coverage;
- consolidated building validator rejects transition anchors that reference missing floors;
- PCG layouts run through the same consolidated validator as authored layouts;
- root W55 package notes moved to `docs/handoffs/`;
- package/baseline creation now hard-fails when the root cleanliness validator fails.

## Root contract

Only these files are permitted at repository root:

- `.gitignore`
- `Cargo.lock`
- `Cargo.toml`
- `README.md`
- `HavenwildTools.cmd`

Run Control Center option **19 — Root cleanliness audit** before the build checkpoint if applying through any nonstandard transport. Normal project packaging now runs the same validator automatically.

## Local gate

1. `2. Build all`
2. `10. Run tests`
3. `19. Root cleanliness audit`

Do not advance to W55R9D/R10 until all three are green.
