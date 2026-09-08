# Pass 148E — Universal Content Browser

The native editor now exposes a category-neutral Content Library dock tab backed by recursively discovered asset-pack manifests.

The browser is additive to the existing production Asset Palette. The palette remains the fast authoring surface for currently bound assets; the Content Library is the authoritative inspection surface for every mounted, disabled, reference-only, partially configured, and production-ready provider.

## Filters

- free-text semantic, asset, pack, and tag search;
- pack provider;
- any `AssetCategory`;
- production-enabled state;
- approved license state;
- runtime readiness.

## Stable identity

Every row preserves pack, category, asset, source, and variant identity. Source-local atlas coordinates and source paths remain attached to their provider rather than being flattened into a global atlas.

## Safety

Reference-only packs remain visible for inspection but are not promoted into production resolution. The browser does not contain LPC-, terrain-, or pack-name-specific branches.

## Follow-on

Pass 148F will connect browser selection and semantic queries to runtime, PCG, F3 placement, animation, audio, UI, inventory, and object-placement resolution through one shared registry.
