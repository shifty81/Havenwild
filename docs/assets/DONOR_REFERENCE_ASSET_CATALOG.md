# Havenwild Donor Reference Asset Catalog

Pass 21 adds a donor/reference catalog for third-party asset packs that are useful for learning, editor browsing, engine tile-size adaptation, and future Havenwild-original tile creation.

This does **not** change the raw asset policy:

- raw third-party packs stay quarantined or user-supplied
- raw donor sheets are not copied into runtime content by default
- blocked/non-commercial/free-only packs stay reference-only
- promotion into runtime requires license policy, metadata, attribution, and release-gate validation
- the future pixel editor may use donor packs as side-by-side reference, not as a way to trace restricted pixels into original Havenwild art

## New catalogs

```text
content/assets/catalog/havenwild_asset_catalog_v0_1.json
content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json
content/assets/pixel_editor/pixel_editor_reference_workbench_v0_1.json
```

## Why this exists

The project now has many useful donor packs with different grid sizes:

- 16×16 forest/interior/icon references
- 32×32 Havenwild-compatible terrain and icon packs
- 40×40 and 48×48 Pipoya world tilesets for editor scaling/adapter tests
- animation and character paper-doll references
- blocked/non-commercial packs that are still useful for coverage planning

The editor and in-game dev editor need one safe place to discover these sources without accidentally treating them as shippable runtime assets.

## Editor behavior target

The standalone editor can show all donor records with source policy badges.

The in-game editor can show donor references only in dev/editor mode. Blocked sources cannot spawn runtime tiles or be included in commercial builds.

The future Lite Pixel Editor panel can pin a donor reference beside a blank Havenwild source sheet, then author original 32×32, 32×64, or animation metadata-backed assets.

## Runtime rule

Runtime default is `not_loaded_by_default` or `blocked`. Only explicitly baked, metadata-backed, policy-valid prototype assets may be made available in dev runtime.

## Validator

Run:

```powershell
python tools/automation/validation/checks/assets/Validate-DonorReferenceAssetCatalogV27.py
```

The validator checks source IDs, blocked-source policies, tile grid declarations, editor visibility contracts, unified catalog indexes, and pixel-editor blocked actions.
