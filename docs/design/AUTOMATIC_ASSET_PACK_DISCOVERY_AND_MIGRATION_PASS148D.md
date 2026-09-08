# Pass 148D — Automatic Asset-Pack Discovery and Existing Content Migration

Havenwild no longer requires Rust registration for each content provider. The registry recursively discovers `pack.json` manifests from project, user, and mod roots, validates them, orders required dependencies, and mounts compatible packs by stable identity.

## Discovery roots

- `content/asset_packs` — project-owned and shipped packs.
- `user/asset_packs` — locally authored/imported packs.
- `mods/asset_packs` — optional installed content packs.

Disabled or reference-only packs remain discoverable for inspection and import but do not enter the production resolver unless explicitly requested. Duplicate IDs, invalid manifests, unresolved dependencies, and dependency cycles produce structured discovery records.

## Migrated providers

The previous monolithic project content is represented by independent manifests:

- `havenwild_core` — umbrella/base dependency.
- `havenwild_worldgen` — terrain, water, roads, and generated world content.
- `havenwild_characters` — player and character animation sources.
- `havenwild_objects` — objects, buildings, trees, and foliage.
- `havenwild_interface` — UI skins and editor interface sources.
- `havenwild_audio` — sound and music providers.
- `lpc_revised` — mounted external/reference provider pending production licensing review.

The manifests are additive compatibility providers. Existing runtime registries remain active until Pass 148F routes consumers through the universal registry.

## Permanent rule

Adding another asset library requires a manifest or importer output, not a new global validator or Rust registration branch. Generic pack validation owns schema, licensing, source identity, dependency, and semantic-index checks.
