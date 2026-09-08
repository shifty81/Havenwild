# Havenwild W43C — Estate Visual Authority Closure

W43C addresses the Farmstead screenshot regressions without breaking compatibility IDs.

- `farmstead` remains the internal/legacy scene code;
- user-facing labels now present **Estate**;
- the legacy starter generator delegates to an Estate development fixture;
- the fixture no longer emits exterior Wall/WoodFloor/GreenhouseZone or Greenhouse/Door/CaveEntrance placeholder objects;
- the native Scene Editor no longer uses `live_autotile_16_32.png` as production terrain fallback artwork.

Unsupported production artwork now remains unresolved/fail-closed instead of leaking cyan/gray debug tiles into Estate.

Validation: `Validate-EstateVisualAuthorityClosureV1.py`.
