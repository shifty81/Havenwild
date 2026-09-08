# Havenwild External Asset Pack Workflow — Pass 66

## Goal

Allow a very large local asset archive to be fully inventoried and exposed to Havenwild's native Pixel Studio without embedding the raw pack in every source ZIP or application build.

## Directory model

The raw archive is extracted outside the repository:

```text
~/HavenwildAssetLibrary/
  packs/
    asset_pack/
      raw/                 # immutable extracted files
      catalog/
        asset_pack.json    # full machine-local inventory
```

The repository receives only:

```text
.local/havenwild_external_asset_roots.json          # machine-local, ignored
content/assets/intake/external_pack_indexes/*.json  # compact metadata indexes
```

Raw assets are not copied into `Build/HavenwildClient` or `Build/HavenwildEditor`.

## Initial intake

From Git Bash:

```bash
cd /c/Users/Shifty/Desktop/havenw

./tools/build/Build.sh asset-pack-prepare \
  "/c/Users/Shifty/Downloads/Asset Pack.zip" \
  --library-root "/h/HavenwildAssetLibrary" \
  --pack-id "havenwild_master_asset_pack" \
  --display-name "Havenwild Master Asset Pack" \
  --license-status unknown_requires_review
```

When the entire archive is confirmed CC0, use:

```bash
--license-status cc0
```

Do not mark mixed or uncertain packs CC0 simply because some files are CC0. Split mixed packs into separate roots or preserve `unknown_requires_review` until each source/license chain is audited.

## What the preparation command does

1. Verifies the ZIP.
2. Prevents ZIP path traversal.
3. Extracts every file to the external library.
4. Records SHA-256 hashes and byte sizes.
5. Reads image dimensions, modes, frame counts, and likely grid sizes.
6. Infers broad categories from filenames and paths.
7. Marks every record `cataloged_source_only`.
8. Registers the external root in `.local/havenwild_external_asset_roots.json`.
9. Writes a metadata-only project index.
10. Rebuilds the external sprite-library catalog.

## Pixel Studio access

Launch:

```bash
./tools/build/Build.sh pixel-studio
```

The left source library includes an **External** source group. Opening an external asset is non-destructive. Use **Save Working Copy** before editing. The editable copy is written under:

```text
assets/source/original/pixel_studio/
```

This keeps stable project-owned working data separate from the immutable raw pack.

## Multi-pass promotion plan

### Pass A — Complete inventory

Catalog every file, duplicate, dimension, grid candidate, animation candidate, and likely category. Nothing is promoted automatically.

### Pass B — Normalize folders and identities

Review categories for:

- terrain and transitions
- buildings, roofs, walls, doors, fences, and bridges
- interiors and furniture
- caves and dungeons
- foliage and environmental props
- characters, clothing, armor, hair, and tools
- animals and directional animations
- icons, UI, effects, and portraits

Assign stable source IDs and correct license metadata.

### Pass C — Tile extraction

For tile families:

- realign logical atlas grids
- define cell size and offsets
- identify variants
- define autotile families
- run repeat/seam previews
- publish reviewed tiles into the active terrain catalog

### Pass D — Multi-tile stamps

For buildings and props:

- crop named regions
- define visual footprints
- define collision and interaction footprints
- place pivots and sockets
- preview in scene context
- publish into the Pass 61 stamp catalog

### Pass E — Animation and character assets

For sprite sheets:

- define frame grids
- define directions and clips
- assign pivots, shadows, events, and sockets
- create project working copies
- clean frames in Pixel Studio
- publish validated animation metadata

### Pass F — Runtime verification

Place promoted assets in test scenes and verify:

- editor/runtime atlas parity
- pivots and depth sorting
- collision and interactions
- animation orientation and frame order
- save/load persistence
- client packaging

## Rebuild and audit commands

```bash
./tools/build/Build.sh asset-pack-catalog
./tools/build/Build.sh asset-pack-audit
./tools/build/Build.sh pixel-audit
./tools/build/Build.sh animation-audit
./tools/build/Build.sh all
```

## Compact future source handoffs

After the raw pack is organized locally:

```bash
./tools/build/Build.sh source-rollup
```

This creates a compact source-and-metadata ZIP while excluding machine-local asset roots, saves, recovery data, build output, logs, and quarantined raw packs.
