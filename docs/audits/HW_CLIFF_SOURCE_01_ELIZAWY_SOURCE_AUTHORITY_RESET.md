# HW-CLIFF-SOURCE-01 — ElizaWy Cliff Source Authority Audit

This report is intentionally **non-runtime**. It does not change renderer, worldgen, collision, or editor behavior.

## Source status

- Original art authority: `ElizaWy/LPC pinned source`
- Summer cliff source present: **True**
- Tiled metadata donor status: **missing_optional_metadata_donor**
- Runtime migration status: **audit_only_runtime_migration_blocked**

## Why the current cliff lane is blocked

- **side_entry_ramp_not_certified** (blocker): ElizaWyCliffConnectedRecipeRole::SideEntryRampPending remains source-reference-only.
  - Closure: Re-certify from original ElizaWy sheet plus demo/TSX relationship evidence; do not infer from screenshot.
- **complex_transition_strip_rejected** (blocker): The c8 transition strip is explicitly represented as rejected/source-reference evidence in the current provider/history.
  - Closure: Audit the complete c8 assembly and its valid neighbors before any runtime promotion.
- **foreign_ramp_family_authority** (blocker): A companion LPC grass-top cliff provider and oga_cliff_source remain in the runtime asset graph.
  - Closure: Remove as cliff/ramp visual authority only after source-native ElizaWy replacement is certified.
- **foreign_geometry_coupling** (blocker): Current directional ramp semantics still reference LpcDirectionalCliffRampRole and historical six-cell geometry designed around a 3x4 companion stamp.
  - Closure: Derive connector footprint from certified ElizaWy assembly evidence, not the retired companion stamp.
- **derived_overlay_is_runtime_source** (review): Runtime lpc_cliff_source currently resolves ELIZAWY_SUMMER_CLIFF_SOURCE_PATH, a derived runtime overlay.
  - Closure: Keep original pinned sheet as immutable art authority; derived overlays may only be recipe outputs with lineage.

## Keep

- `straight_south` — c2r7 -> c2r3 repeat -> c2r8 — existing demo-grounded W14 authority
- `south_west` — c1r7 -> c1r3 repeat -> c1r8 — existing demo-grounded W14 authority
- `south_east` — c3r7 -> c3r3 repeat -> c3r8 — existing demo-grounded W14 authority
- `narrow_cave` — c6r9-c6r11 — existing source-native certified feature column
- `ladders` — c11r9-c11r11 and c13r9-c13r11 — existing source-native certified feature columns

## Explicitly not done in this pass

- No ramp renderer patch.
- No six-cell replacement artwork.
- No new cliff pixels.
- No change to structural collision.
- No promotion of the Tiled donor atlas as an art source.
- No deletion of old providers until a source-native replacement is certified.

## Migration sequence

1. Acquire/locate the configured Tiled donor archive in governed quarantine; do not replace ElizaWy source art.
2. Parse TSX/Wang/property/animation/collision metadata with Havenwild's existing Tiled semantics.
3. Map donor atlas tiles back to original ElizaWy 32x32 cells/stamps using exact pixel hashes where possible.
4. Cross-check ambiguous c8/side-entry/terminal relationships against ElizaWy official Summer demo and Test Landscape.
5. Write a certified source-native assembly catalog with source rect, footprint, anchor, valid neighbors and evidence lineage.
6. Only then migrate the runtime cliff resolver from hand-authored guesses to certified assembly selection.
7. After migration proves parity, remove companion ramp visual authority and unused foreign runtime texture loading.
