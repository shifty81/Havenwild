# Pass 66 — External Asset Pack Intake and Source Rollup

Pass 66 prepares Havenwild for a separately supplied large `Asset Pack.zip`.

## Implemented

- Safe external ZIP extraction.
- Machine-local external asset library under a user-selected path.
- Full file/image inventory with hashes, dimensions, frame counts, likely grids, categories, and promotion state.
- Metadata-only project indexes.
- Pixel Studio external-source scanning through `.local/havenwild_external_asset_roots.json`.
- External source labels and retained license metadata.
- Non-destructive project working-copy workflow.
- External sprite catalog support for both committed and machine-local roots.
- Bash commands for prepare, catalog, audit, and compact source rollups.
- Source-rollup policy excluding raw external packs, saves, recovery data, logs, and build output.
- V83 regression validator.
- Codex-specific asset-pack handoff instructions.

## Important boundary

The actual `Asset Pack.zip` was not supplied with this pass, so no claim is made that its assets have already been inventoried or promoted. The latest source is ready for Codex to receive alongside the archive and perform that work locally over multiple passes.
