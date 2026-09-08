# Prototype Asset Import Adapters

Pass 20 adds no-raw-copy import adapter metadata for the safest audited prototype assets.

These adapters do **not** copy raw third-party art into Havenwild runtime folders. They describe how a local/user-supplied or quarantined source pack may later be baked into processed prototype outputs with attribution and release restrictions preserved.

## Current adapters

| Adapter | Source | Use |
|---|---|---|
| `adapter.pipoya_world_tileset_32.v0_1` | Pipoya RPG World Tileset 32/40/48 | 32px terrain, water, cliff, road, Tiled fixture |
| `adapter.free_pixel_food_icons_32.v0_1` | Free Pixel Food / Food.png | 16px food icons scaled to 32px |
| `adapter.pixel_mart_icons_32.v0_1` | Pixel Mart | 32px item/shop/inventory icons |

## Rules

- Raw third-party archives stay in `assets/reference_quarantine/third_party/...` or remain user-supplied outside the repo.
- Processed prototype outputs must have `.hhasset.json` metadata.
- Non-commercial/free-only packs are not adapter-eligible for runtime builds.
- Every processed output needs a release gate and no-standalone-asset-export restriction.
- `runtimeDefault` stays `false` until a deliberate project decision promotes the asset.

## Next implementation stage

A later bake command can read these adapter manifests, ask the user for a local/quarantined source path, generate the processed atlas, then write a bake report under `WORKSPACE/generated/prototype_imports/`.
