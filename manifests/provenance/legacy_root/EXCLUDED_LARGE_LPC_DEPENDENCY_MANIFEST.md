# Havenwild Pass 93 Compact Codex Source Rollup

This compact source rollup contains the complete Havenwild source, build scripts, generated runtime assets, Pass 93 summer terrain mappings, compressed LPC catalog bundles, validators, manifests, documentation, and previews.

## Intentionally excluded

- `assets/source/licensed/lpc_revised/` — the large raw LPC dependency tree.
- `content/assets/lpc/lpc_slice_catalog_v0_1.json` — the 50+ MB uncompressed virtual-slice catalog; the `.json.gz` form remains included.
- `content/assets/intake/external_pack_indexes/elizawy_lpc_main.json` — the large regeneratable intake index.

These exclusions keep the source handoff small enough for reliable download. They do not remove the Pass 93 mappings or generated runtime atlases.

## Use

For an existing Havenwild working tree that already contains the LPC source dependency, apply the Pass 93 overlay patch instead of replacing the whole tree.

For a new compact checkout, restore your existing `assets/source/licensed/lpc_revised` directory before running full LPC rebakes. Then run:

```bat
tools/build/Build.cmd lpc-summer-map
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

The raw LPC source remains external/reconstructable and should not be duplicated in every ChatGPT/Codex source rollup.
