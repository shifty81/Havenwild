# Havenwild V7 Animated Medium-Water Test Audit — Pass167Z73

## Windows result

The Z72 workstation build passed source validation, `cargo fmt --check`, workspace Cargo check, and strict Clippy. `haven_assets` then completed 65 of 66 tests. The only failure compared the ocean boundary's selected V7 medium-water animation cell with the first quiet V7 medium-water cell.

## Audit conclusion

The differing rectangles were both complete pure `Water` entries in the source-certified V7 atlas:

- resolved animated cell: `AtlasRect { x: 2109, y: 2109, w: 32, h: 32 }`;
- first quiet/canonical cell: `AtlasRect { x: 409, y: 1, w: 32, h: 32 }`.

The runtime was behaving as designed. The test encoded an invalid single-rectangle assumption for a material that intentionally has multiple authored animation variants.

## Resolution

The regression test now validates membership in the complete pure V7 `Water` variant set while separately asserting preserved `OceanDeep` semantics and exact mixed V7 boundary overlays.
