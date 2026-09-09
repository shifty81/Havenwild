# PCC-ASSET-SCALE-02 — Compact Catalog + Persistent Inventory Index

The first complete SMART LPC scan proved the staged scanner works, but also
produced a 109+ MB JSON catalog because every one of the 64k PNG inventory
records and every deep-analysis payload was duplicated into one file.

SCALE-02 makes SQLite the detailed operational index and keeps the normal JSON
catalog compact.

## Default scan output

`asset-catalog.json` now contains:

- source/mount identity;
- scan profile and performance;
- summary/domain counts;
- compact deep-sheet references;
- Tiled evidence;
- the assembly index;
- deferred/error records.

Detailed per-file records and full deep-analysis payloads remain in:

`artifacts/asset-intake/cache/pcc_asset_cache.sqlite`

Use `--catalog-detail full` only when a monolithic forensic export is
specifically required.

## Persistent inventory cache

Unchanged PNGs now reuse their cached dimensions, classification and variant
family. A second scan still enumerates/stats the source tree to detect changes,
but it does not reopen all 64k PNGs merely to reread IHDR dimensions.

## SQLite file index

The cache now has a `catalog_file` index with source root, relative/logical/
physical paths, hash, domain, analyzer route, variant family, deep-analysis
state, dimensions and byte size. This becomes the detailed query surface used
by later character/terrain/structure domain analyzers.

## Compatibility

Catalog validation accepts both v1 and v2 catalog schemas. Compact v2 catalogs
preserve the assembly index expected by prefab/certification operations.
