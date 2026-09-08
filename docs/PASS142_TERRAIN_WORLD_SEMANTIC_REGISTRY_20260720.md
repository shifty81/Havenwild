# Pass 142 — Terrain and World Semantic Registry

## Decision

`content/worldgen/terrain_world_semantic_registry_v1.json` is the authoritative terrain identity contract moving forward. The earlier `content/assets/terrain_material_registry_v0_1.json` remains read-only compatibility input until all consumers migrate.

## Stable identity rule

- `id`, `code`, and `stableOrdinal` are save/network-facing identities.
- Existing ordinals are never reordered or reused.
- New terrain is appended with a new ordinal.
- Renames use `deprecatedAliases`; they do not silently replace codes.

## Ownership rule

Every material declares `authored`, `generated`, or `deferred` lifecycle ownership. Generated terrain uses `recompute` regeneration and names its authoritative system. Editor paint modes must agree with lifecycle ownership.

## Consumer rule

Runtime, editor, world generation, persistence, asset lookup, transition resolution, and validators consume this registry or generated code derived from it. New parallel terrain lists are not permitted.

## Asset/legal rule

Production source art must be Havenwild-authored or verified compatible with commercial redistribution. Reference-only, unknown-license, GPL, noncommercial, and unapproved share-alike sources cannot be promoted as production assets.

## Validation

`tools/automation/validation/checks/terrain/Validate-TerrainWorldSemanticRegistryV142.py` checks stable uniqueness, append-only ordinals, legacy compatibility, TileKind coverage, biome references, asset lookup coverage, ownership rules, and validation-manifest registration.
