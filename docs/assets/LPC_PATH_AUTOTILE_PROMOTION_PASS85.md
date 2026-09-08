# LPC Path Autotile Promotion - Pass 85

Pass 85 promotes Havenwild path tiles into separate live autotile families.

## Fixed From Pass84 Build

- Removed the unused `family_neighbors` import from
  `crates/haven_world/src/autotile/transition_resolver.rs`.
- This addresses the strict-Clippy failure shown in the
  `2026-07-13 07:53:55` build log.

## Path-Family Split

Before this pass, these tiles all shared `TileAutoGroup::Road`:

- `Road`
- `StonePath`
- `MountainPath`
- `Bridge`

That meant the resolver could compute a mask, but every path-like tile was
bound to the same generic road atlas row.

They now resolve to separate same-family groups:

| TileKind | TileAutoGroup |
| --- | --- |
| `Road` | `Road` |
| `StonePath` | `StonePath` |
| `MountainPath` | `MountainPath` |
| `Bridge` | `Bridge` |

## Regenerated Atlas

`tools/automation/terrain/Generate-LiveAutotileAtlas.py` now emits 10 live autotile groups:

- road
- stone_path
- mountain_path
- bridge
- wood_floor
- stone_floor
- water
- wall
- cliff
- cave_wall

The generated atlas now contains 160 bindings instead of 112.

## Compatibility

Old saves may contain manual path overrides recorded as `road`, because stone
paths, mountain paths, and bridges previously shared that group. Pass 85 keeps
those old override records usable while automatic adjacency and new overrides
use the split groups.

## Inspector Test Update

The `2026-07-13 08:07:20` Windows build confirmed `cargo check` and strict
Clippy passed after the path split. The remaining failure was an editor
inspector unit test that still placed `StonePath` east of `Road` and expected a
road mask of `0x04`.

That assumption is now invalid by design. The test now verifies:

- Road next to Road reports `Autotile mask: 0x04`.
- Road next to Stone Path reports `Autotile mask: 0x00`.
- Stone Path reports its own `Autotile group: Stone Path`.

## Next Proper LPC Steps

- Split `WoodFloor` and `PlankFloor` into separate rows.
- Split `StoneFloor` and `BrickFloor` into separate rows.
- Promote cave floor, cave wall, wall, cliff, and modular building exterior
  rows from reviewed LPC source cells.
- Replace placeholder topology marks with authored LPC replacement roles where
  available.
- Keep non-tileable props, vegetation, furniture, and town clutter as object or
  stamp assets rather than terrain.
