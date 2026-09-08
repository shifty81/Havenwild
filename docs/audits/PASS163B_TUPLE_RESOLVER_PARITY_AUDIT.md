# Pass 163B Tuple Resolver Parity Audit

## Completed

- Embedded the promoted tuple catalog into the Havenwild world crate.
- Added deterministic exact-signature lookup.
- Added unresolved-signature reporting with no unrelated visual fallback.
- Classified all 31 duplicate signatures.
- Added catalog-count and duplicate-policy consistency checks.
- Added internal-edge, chunk-edge, and wrapped-seam determinism tests.
- Added a project-menu terrain tuple audit command.

## Current catalog contract

- Terrain families: 34
- Mapped tuple entries: 15,653
- Unique tuple signatures: 15,562
- Duplicate signatures: 31
- Canonical duplicate rule: lowest/first generated tile ID

## Remaining terrain parity work

1. Feed runtime-produced semantic corner tuples through this resolver.
2. Feed World Builder painting through the same resolver.
3. Record unresolved tuple telemetry during PCG/runtime execution.
4. Add visual acceptance-map tile-ID comparisons.
5. Add compatibility warnings before deterministic priority fallback.
