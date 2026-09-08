# Havenwild Pass 90E — LPC Terrain Owner-Side World Test Hotfix

## Purpose

Pass 90E closes the three remaining `haven_world` test failures exposed after Pass 90D. The fixes preserve the Pass 90 owner-side LPC transition contract and repair a real procedural-island edge condition where smoothing could regrow land against a missing scene slot.

## Corrections

### Terrain debug test

The debug test now inspects a shallow-water owner cell beside grass. Under the Pass 90 contract the water/depth cell owns the LPC bank overlay; the adjacent grass cell deliberately emits no competing transition.

### Transition preview test

The preview test now resolves the active Pass 90 rule ID `shallow_water_touching_sand_bank` instead of the removed pre-Pass-90 ID `sand_touching_water_wet_sand`.

### Missing scene slots remain open water

`island_coastline` now reasserts an open-water boundary:

1. after the initial land mask;
2. after every smoothing pass;
3. after emergency land seeding.

Any occupied tile touching the outside of the raster or an unoccupied neighboring scene cell is forced out of the land mask. This prevents cellular smoothing from regrowing grass along a missing scene slot while still allowing shallow-water and beach bands to form immediately inward.

A direct coastline regression test now verifies that the occupied edge beside a removed scene slot remains deep or shallow water after smoothing. The existing L-shaped island-assembly test remains active.

## Validation

Passed in the packaging environment:

- architecture validation: 183 Rust files;
- content validation: 218 JSON files;
- Havenwild open-world preset;
- editor validators through V79 before aggregate timeout;
- validators V80–V97 individually;
- deterministic Pass 90 terrain atlas promotion.

The packaging environment does not include a Rust toolchain. The authoritative final check is:

```bat
tools/build/Build.cmd all
```

Expected progression:

```text
cargo fmt        PASS
cargo check      PASS
cargo clippy     PASS
cargo test       PASS
validators      PASS
release apps     BUILT
```

## Scope boundary

Pass 90E changes no LPC source coordinates, atlas pixels, save schema, scene dimensions, camera behavior, or transition priorities. It only updates stale tests and guarantees the procedural coastline boundary promised by the existing missing-scene contract.
