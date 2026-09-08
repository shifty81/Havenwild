# Pass 148C — Category Metadata Contracts and Full Tiled Normalization

## Purpose

Pass 148C layers typed, category-specific metadata over the universal `AssetPack` and importer foundation without splitting the registry into category-specific asset silos.

All assets retain the same stable identity:

`pack_id + category + asset_id + source_id + variant_id`

Category metadata is stored as a typed contract attached to the generic `AssetDefinition`.

## Initial typed categories

- terrain
- tile objects
- buildings
- characters
- animations
- items
- audio
- UI

The contract registry is intentionally extensible. Existing categories such as crops, trees, clothing, armor, tools, weapons, animals, NPCs, effects, music, recipes, biomes, world generation, scenes, interiors, caves, dungeons, and editor templates continue to use the universal asset model and can receive typed contracts in later migrations without changing stable references.

## Tiled TSX normalization

The TSX provider now preserves and normalizes:

- tileset dimensions, columns, margin, and spacing;
- per-tile class/type identity hints;
- typed custom properties;
- tile probability;
- animation frames and durations;
- collision object groups;
- Wang-set assignments and eight-position Wang IDs;
- source-local atlas coordinates.

Wang assignments can populate terrain category metadata, but only when the import request classifies the source as terrain. Other categories retain Wang information under generic Tiled metadata rather than being forced into terrain semantics.

## Safety rules

- Raw sheets remain manual-only unless a profile or reviewer assigns metadata.
- Tiled metadata improves runtime readiness but does not grant production approval.
- Licensing remains pack-level and independent from technical import readiness.
- Category metadata must match the asset category.
- Invalid footprints, empty required identifiers, empty animation clips, and missing event/role values fail category validation.

## Next migration boundary

Pass 148D should migrate current Havenwild content into independent normalized packs and build a registry loader that mounts all discovered pack manifests without category-specific Rust registration code.
