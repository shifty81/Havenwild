# Codex handoff — Havenwild external Asset Pack intake

Use the supplied latest Havenwild source ZIP as the baseline and the separately supplied `Asset Pack.zip` as a machine-local external source library.

## Non-negotiable rules

- Do not embed the raw full asset archive in routine source rollups.
- Do not copy unknown-license assets into shipping runtime output.
- Catalog every file even when it is blocked from promotion.
- Preserve immutable raw files and hashes.
- Pixel Studio must open external assets as source-only.
- Editing begins only after creating a project working copy.
- Promotion into tiles, stamps, animations, icons, or runtime atlases is explicit and metadata-backed.
- Preserve stable IDs when repacking atlases.
- Keep Havenwild separate from Open2D.

## First command

```bash
./tools/build/Build.sh asset-pack-prepare "/absolute/path/to/Asset Pack.zip" \
  --library-root "/absolute/path/to/HavenwildAssetLibrary" \
  --pack-id "havenwild_master_asset_pack" \
  --display-name "Havenwild Master Asset Pack" \
  --license-status unknown_requires_review
```

Use `--license-status cc0` only when the whole archive has been explicitly confirmed CC0. Mixed packs must remain review-gated.

## Required work sequence

1. Run the full pack inventory and verify file counts and hashes.
2. Audit duplicate and near-duplicate sheets.
3. Produce a KEEP / PROMOTE / REWORK / REFERENCE / BLOCK matrix.
4. Normalize source categories without modifying immutable raw files.
5. Process terrain families first.
6. Process multi-tile buildings/props second.
7. Process animals/characters/animation sheets third.
8. Process icons/UI/effects last.
9. Add validators for every promoted family.
10. Run `./tools/build/Build.sh all` after each coherent pass.
11. Produce compact source rollups with `./tools/build/Build.sh source-rollup`.

## Expected outputs per pass

- updated source ZIP
- source diff
- handoff markdown
- catalog statistics
- promoted asset manifest
- validation report
- list of raw assets intentionally left external
