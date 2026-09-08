# Pass 148I — Stable Texture Cache and Renderer Binding Migration

Pass 148I adds a runtime texture cache keyed by stable asset references and resolved source paths.

## Rules

- Semantic assets resolve through the mounted production asset registry.
- A physical texture source is loaded once per normalized source path.
- Multiple semantic assets may share the same loaded texture.
- Renderer-facing atlas fields remain temporary compatibility aliases.
- Missing semantic providers produce explicit, retained legacy-fallback records.
- Stamp sheets use the same source-path cache instead of loading independently.

## Initial migrated bindings

- `terrain.grass`
- `terrain.sand`
- `terrain.path.road`
- `object.catalog.runtime`
- `character.player.base`

## Remaining migration

Transition, world-paint compatibility, UI, preview, and remaining stamp/source contracts should gain semantic manifests before their direct compatibility paths are removed.
