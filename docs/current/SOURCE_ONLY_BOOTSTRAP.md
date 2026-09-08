# Havenwild Source-Only Bootstrap

A source-only archive contains the Rust workspace, content contracts, scripts, validators, documentation, and license/source metadata while excluding binary/raw runtime assets and all `WORKSPACE/` machine-local state.

On Windows from repository root:

```bat
HavenwildTools.cmd
```

Use dependency sync/audit when required, then Build All. Pinned ElizaWy and Universal LPC dependencies are reconstructed through their locked dependency workflows rather than duplicated into every source-only handoff.

Canonical content paths after Pass167Z106N5:

- animation metadata: `content/animations/`
- worldgen packs: `content/worldgen/packs/`
- asset packs/providers: `content/asset_packs/`
- runtime/editor generated assets: `assets/generated/`
- reproducible local indexes/caches: `WORKSPACE/generated/` (not packaged)

Generate a source-only archive with the source-only packaging command exposed by the build tooling.
