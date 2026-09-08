# Havenwild Pass 96F — Editor Registry-Derived Tests Hotfix

The Pass 96E build passed asset generation, formatting, workspace checking,
strict Clippy, and all 24 `haven_assets` tests. Two `haven_editor` tests still
encoded retired assumptions.

Pass 96F changes them to use the loaded runtime registries:

- generated-asset summary accepts the registry's active manifest identity,
  including the supported LPC-only direct-terrain fallback;
- stamp transaction coverage selects a real entry from the current LPC-only
  stamp registry and resolves placement/erase coordinates from the placed
  stamp's stable ID and visual footprint.

V110 prevents the removed mountain-tavern ID and fixed optional-manifest name
from returning to these tests.

Extract this complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```
