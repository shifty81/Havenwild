# Havenwild Pass 102 - Asset Audit Build Order Hotfix

Pass 102 continues from Pass 101 / V115 lineage.

## Why

`tools/build/Build.cmd all` reached V115 after V103 through V114 passed, but V115 expected
`docs/assets/HAVENWILD_ASSET_UTILIZATION_AUDIT_PASS100.md` before the main build
had generated it.

The dedicated `asset-utilization-audit` command already ran the builder before
the validator. The main `all` pipeline needed the same ordering.

## Changed

- `tools/build/Build.sh all` now builds the Havenwild asset utilization audit before V115.
- V115 self-generates the report when run directly from a clean extraction.
- The source rollup script keeps excluding Python cache files.
- No terrain art, autotile resolver behavior, or editor palette behavior changed.

## Expected next build

The next `tools/build/Build.cmd all` should move past:

- V108 edge-signature seams
- V111 authored replacement roles
- V114 paint topology
- V115 asset utilization audit workflow

Any later failure should be treated as the next real blocker, not a lineage
regression.
