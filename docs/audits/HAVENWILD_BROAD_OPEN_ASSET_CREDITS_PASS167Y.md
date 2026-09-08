# Havenwild Pass 167Y — Broad Open Asset Credits

## Purpose

Havenwild now uses a two-layer credit model:

1. a broad master acknowledgment for every contributor attached to the
   commercially approved Universal LPC catalog available to development;
2. an exact per-build ledger for only the attributed source files and generated
   ShareAlike composites actually distributed by that build.

The broad list is additive. It does not replace exact attribution, source links,
license notices, modification records, or ShareAlike obligations.

## Current snapshot

- Approved Universal LPC source records: 13,818
- Conditional CC-BY-SA records: 2,038
- Unique broadly acknowledged contributors: 71

## Runtime

The title menu includes **Open Asset Credits [C]**. The credits screen presents
Havenwild's broad LPC/OpenGameArt acknowledgment and explains where complete
machine-readable and release-specific records are distributed.

## Build and release tools

- `tools/automation/characters/Build-UniversalLpcBroadCreditsV167Y.py`
- `tools/automation/release/Build-HavenwildOpenAssetCreditsV167Y.py`
- `tools/automation/assets/Build-HavenwildOpenAssetCredits.cmd`

The release generator writes:

- `OPEN_ASSET_CREDITS.txt`
- `OPEN_ASSET_CREDITS.csv`
- `OPEN_ASSET_CREDITS.json`
- broad master contributor TXT/CSV
- catalog summary and license notices

## Policy boundary

Broad pre-crediting is permitted as additional acknowledgment, but Havenwild
continues to generate exact credits for shipped assets. This avoids implying
that broad credit alone satisfies asset-specific attribution requirements.
