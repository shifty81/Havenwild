# Havenwild Pass 96B — Pre-Cargo Runtime Status Ordering Hotfix

The Pass 96A build correctly restored and baked 176 transition records, but
V103 generated its complete summer ledger before the restore step. V107 then
read the stale `mapped_next` status and stopped before Cargo began. Because
Cargo had not started, no `target` directory was expected.

Pass 96B moves deterministic metadata restoration ahead of V103 generation and
marks these canonical contract groups active before building the ledger:

- `summer_sand_over_wet_sand`;
- `summer_pebble_path_fill`;
- `summer_pebble_path_over_dirt`.

Extract the complete source rollup over the repository. Delete `target` only if
it exists, then run:

```bat
tools/build/Build.cmd all
```

V107 should now pass after the 176-record bake, followed by V108 and then the
Cargo stages that create `target`.
