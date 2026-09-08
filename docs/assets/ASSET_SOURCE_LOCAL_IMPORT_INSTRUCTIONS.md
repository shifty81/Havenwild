# Asset Source Local Import Instructions

Pass 25 adds per-source local placement instructions for donor/reference asset packs.

The goal is to let the in-game **Assets** editor tab tell a developer exactly where to place an original zip/sheet before running the safe prototype bake dry-run. This is not a runtime import approval path by itself.

## Instruction manifest

```text
content/assets/prototype_imports/prototype_asset_local_import_instructions_v0_1.json
```

Each record is keyed by `externalSourceId` and records:

- preferred `WORKSPACE/imports/third_party/<source-slug>/` path
- preferred quarantine path
- accepted original archive/sheet filenames
- local import status: candidate, blocked/reference, or unverified
- dry-run command
- runtime-use rule copied from the external source policy

## Editor behavior

In dev mode, open the in-game editor and switch to **Assets**.

The selected donor/source detail now shows:

- local import path
- expected filename(s)
- source availability status
- bake report status
- prototype/reference/blocked policy

The **Path** button or **I** hotkey writes a short placement instruction to the editor status/log line.

## Safety rules

- Raw third-party assets stay user-supplied or quarantined.
- Do not copy donor files into `assets/processed/` by hand.
- Blocked, non-commercial, and unverified sources may be visible as learning/reference donors, but they must not bake into runtime assets.
- The dry-run report is status-only and safe to commit; it must not include pixels.
- Runtime use still requires bake, metadata, license review, attribution/no-standalone-export rules, and explicit promotion.

## Expected local placement examples

```text
WORKSPACE/imports/third_party/pipoya_free_rpg_world_tileset_32_40_48/Pipoya RPG World Tileset 48x48 40x40 32x32.zip
WORKSPACE/imports/third_party/henrysoftware_free_pixel_food_cc0/FreePixelFood.zip
WORKSPACE/imports/third_party/ghostpixxells_pixel_mart_cc0/Pixel_Mart.zip
```

Reference-only/non-commercial packs can still be cataloged for learning, but the bake gate should continue to refuse them unless a new commercial/verified source record is added.
