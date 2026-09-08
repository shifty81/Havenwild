# Havenwild Third-Party Asset Intake Policy

Generated: 2026-07-09  
Pass: Asset Intake / Third-Party Quarantine Pass 19

## Purpose

Havenwild can use third-party art packs for reference, editor tests, prototype fixtures, and temporary runtime art only when the license and repository policy are explicit.

Raw third-party assets are not treated as project-owned art. They must stay quarantined or user-supplied until a source record, license record, and metadata-backed promotion record exist.

## Required folders

```text
assets/reference_quarantine/third_party/<source_id>/
assets/processed/prototype_tiles/<source_id>/
assets/processed/prototype_props/<source_id>/
assets/processed/prototype_characters/<source_id>/
content/assets/external_sources/external_asset_sources_v0_1.json
content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json
```

## Allowed states

| State | Meaning |
|---|---|
| `reference_quarantine_only` | Reference only. Do not import into runtime. |
| `quarantine_or_user_supplied_raw` | Raw pack may exist locally/quarantined but should not be shipped as public runtime content by default. |
| `candidate_allowed_for_prototype` | Can be processed into metadata-backed prototype assets if license and attribution are preserved. |
| `blocked_free_version_non_commercial_only` | Do not use in commercial runtime. Paid-license replacement requires a new source record. |
| `blocked_until_license_chain_restored` | Do not promote until author/license/attribution chain is complete. |

## Promotion gates

Before any third-party asset is promoted from quarantine into runtime/prototype content:

1. The asset source must exist in `external_asset_sources_v0_1.json`.
2. The license status must allow the requested use.
3. The raw files must remain quarantined or user-supplied.
4. The processed output must have `.hhasset.json` metadata.
5. The metadata must record author, source URL, archive name, license status, export restrictions, anchor, footprint/collision if relevant, and intended use.
6. Release builds must reject non-commercial/free-version blocked sources.

## Current decisions from audits

- Pipoya 32x32 RPG tileset bundle: strongest immediate 32x32 prototype terrain/water/door candidate.
- Seliel/Mana Seed Gentle Forest: good autotile/waterfall/Tiled fixture, but needs a 16x16-to-32x32 adapter.
- Seliel/Mana Seed character base demo: useful compositor/reference fixture, not a direct Havenwild 64x96 8-direction player contract match.
- rowdy41 Wood Garden / Small Forest: useful prototype props/foliage candidates with metadata.
- shubibubi free packs: reference/quarantine only for the free versions; paid complete-license records must be separate.
- LPC/OpenGameArt-looking loose files: blocked until exact author/license/attribution chain is restored.

## Validator

Run:

```powershell
python tools/automation/validation/checks/assets/Validate-ExternalAssetIntakeV25.py
```

The validator checks source IDs, policy consistency, quarantine paths, blocked-source safety, import queue references, and runtime-promotion hazards.
