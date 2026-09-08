# Havenwild Pass 167X — Live Character Studio and Universal LPC Usage Tracking

## Purpose

This pass turns the Universal LPC commercial and ShareAlike authority from a data-only intake into a visible, first-class Character Studio workspace inside the single Havenwild native editor executable.

It also closes the release-accounting gap by generating the exact CC-BY-SA usage manifest from saved character recipes and generated composite manifests.

## Native editor integration

Character Studio is now registered as a seventh editor workspace beside World Routes, World Surface, Scene Bank, Scene Editor, Pixel Studio, and Animation Studio.

The workspace provides:

- Player, NPC, Population, and Validation modes;
- Male and Female filters;
- Child, Teen, Adult, and Elder filters;
- preferred-commercial-only mode by default;
- explicit opt-in to verified CC-BY-SA records;
- component-slot filtering;
- searchable source, tag, category, and author fields;
- visible ShareAlike badges;
- source, author, license, tag, URL-count, and mount-state inspection;
- live reload of the locally generated Universal LPC authority.

The editor loads:

`WORKSPACE/generated/universal_lpc_character_authority_v167w.json`

The large source repository remains mounted locally under:

`assets/source/licensed/universal_lpc_generator`

The native editor does not duplicate the full source repository into patches or the permanent project tree.

## License pool behavior

The workspace defaults to the preferred commercial pool:

- CC0;
- OGA-BY;
- CC-BY.

The `Include CC-BY-SA` control admits the 2,038 verified conditional records. A selected ShareAlike layer is clearly marked and remains subject to exact dependency tracking and the open-asset release bundle.

Player mode blocks obvious monster-only tags such as zombie, skeleton, lizard, wings, and tail. NPC, Population, and Validation modes may inspect the broader catalog.

## Exact usage tracking

Added:

`tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py`

The script scans saved recipes, authored-character data, save data, and character composite-cache manifests. It records only CC-BY-SA sources actually referenced by production data.

Default output:

`WORKSPACE/generated/universal_lpc_usage_manifest.json`

The manifest includes:

- exact source paths;
- modification and override placeholders;
- generated composites containing ShareAlike dependencies;
- source dependency lists;
- scanned-file counts and parse diagnostics.

The release exporter now builds this manifest automatically when `--usage-manifest` is omitted. The resulting open-asset bundle therefore defaults to exporting only used CC-BY-SA material rather than all 2,038 conditional records.

## Bootstrap normalization

`tools/automation/characters/Bootstrap-UniversalLpcGenerator.cmd` now builds the v167w authority, then generates the usage manifest in the same normalized setup flow.

Convenience wrapper:

`tools/automation/characters/Build-UniversalLpcUsageManifest.cmd`

## Current boundary

This pass provides the live catalog, filtering, license visibility, and exact usage accounting. The next Character Studio pass should add source-backed texture previews, editable typed CharacterRecipe assembly, deterministic NPC reroll/locking controls, composite-cache generation, and direct layer handoff to Pixel Studio.
