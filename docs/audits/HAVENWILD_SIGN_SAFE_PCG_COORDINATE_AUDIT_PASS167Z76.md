# Havenwild Sign-Safe PCG Coordinate Audit — Pass 167Z76

## Finding

`ProjectSceneId::new` intentionally normalizes hyphens and whitespace into underscores. The Z75 test constructed a raw PCG ID with `-2`, but the stored code no longer contained a minus sign. The parser consequently returned positive `2`.

## Decision

Do not weaken project-wide scene-ID normalization. Encode signed PCG partition coordinates in identifier-safe tokens instead.

## Locked contract

- `n#` means a negative coordinate.
- a decimal token means a non-negative legacy/current coordinate.
- `p#` is accepted as an explicit positive token.
- PCG IDs are generated through one helper rather than direct integer formatting.
- region slugs continue to be parsed from the right and may contain underscores.
- generated-surface fallback IDs keep their existing `p#`/`n#` convention.

## Remaining open-world work

The runtime still needs composite rendering of neighboring exterior partitions, a permanently global exterior camera, cross-partition actor/object/collision submission, and removal of remaining active-scene exterior assumptions.
