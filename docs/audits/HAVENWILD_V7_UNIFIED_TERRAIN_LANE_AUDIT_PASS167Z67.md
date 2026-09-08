# Havenwild V7 Unified Terrain Lane Audit — Pass 167Z67

## Finding

The normalized V7 tuple atlas remained pixel-pure, but the active terrain presentation was not style-pure. Runtime and editor paths could layer ElizaWy shallow/deep cells, generic generated transition artwork, old generated palette previews, or non-grass detail alternates over V7 semantic terrain.

## Certified V7 lane

The V7 landmass uses one source-pure normalized runtime atlas derived exclusively from:

- `terrain-map-v7.png`;
- `terrain-v7.png`.

The certified lane covers quiet owner fills and exact mixed corner tuples for V7 grass, dirt, roads, sand, gravel, mountain path, rock ground, cave floor, freshwater shallows, marine shallows, water, and deep water.

## Isolation requirements

- No active V7 terrain renderer may sample ElizaWy terrain sheets.
- No generic transition atlas may render over V7 terrain.
- No cross-family fallback is permitted for unsupported tuples.
- Native editor previews must use the same normalized V7 atlas as runtime.
- `WetSand` is a hidden legacy alias to V7 Sand only.
- One landmass selects one terrain style lane.
- A future ElizaWy mainland atlas must remain separately normalized and certified.

## Detail requirements

- Non-grass fills use quiet authored entries.
- A larger authored mark is an atomic object/stamp, not a fill alternate.
- Atomic details place completely or are skipped.
- Partial cell fragments, cropped assemblies, and random scatter from multi-cell art are prohibited.

## Legacy scene finding

`farmstead_scene_v0_3` contains historical mixed terrain and `WetSand` cells. It is classified as `legacy_mixed`, remains reference-only, and must be regenerated after terrain lock rather than promoted into the continuous production world.

## Certification targets

- V7 pond and ocean fixtures show exact V7 shallow/deep tuples.
- V7 Sand touches `Water_Shallows_Sand` directly.
- Pebble Shore, Mountain Path, Cave Floor, and Rock Ground remain visually coherent quiet V7 materials.
- F3 and the native editor display the same terrain for the same saved semantics.
- Unsupported tuple diagnostics do not trigger invented or cross-style artwork.
