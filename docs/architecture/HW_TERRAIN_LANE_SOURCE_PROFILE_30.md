# HW-TERRAIN-LANE-SOURCE-PROFILE-30

This pass continues the standalone Havenwild asset-mapper lane after `HW-ASSET-MAPPING-CORRECTION-BRAIN-29R1` went GREEN.

## Goal

Stop treating visual sheet scanning as the authority for terrain. The mapper now begins recording profile-aware mapped cells so Havenwild can bridge:

- current V7 runtime/compatibility terrain provider,
- LPC Revised seasonal terrain sheets,
- ElizaWy cliff sheets,
- LPC directional ramp stamps,
- ElizaWy waterfalls,
- future Ember editor ingest.

## Runtime principle

The renderer should never guess the source tile from pixels at runtime.

Worldgen/editor emits a provider-neutral terrain role. The Terrain Lane resolver returns the exact source sheet and source rectangle to draw.

```text
Terrain role/topology + season/context
  -> Terrain Lane provider resolver
  -> exact source profile
  -> exact source rect
  -> renderer draw
```

## Mapper changes

Mapped-sheet records are upgraded to `havenwild.atlas_mapper_mapped_sheet.v0_5` and now include profile fields per tile:

- `terrain_family`
- `topology_role`
- `layer_role`
- `collision_profile`
- `compatibility_class`

The inspector also surfaces the selected sheet's source profile so the user can tell whether the selected asset is using seasonal terrain, V7 compatibility, cliff, ramp, waterfall, or generic asset mapping logic.

## What this does not do yet

This is not the full world-preview terrain editor. It does not publish seasonal terrain into runtime, and it does not remove V7 fallback. It makes each learned/green-checked tile carry enough structured metadata for the next passes: group boxing, water topology, collision paint, and source-profile validation.

## Ember mirror note

Havenwild remains standalone and commits/pushes through its internal PCC. Ember later mirrors the generic source-profile, mapper, and Terrain Lane contracts from the Havenwild GitHub checkpoint.
