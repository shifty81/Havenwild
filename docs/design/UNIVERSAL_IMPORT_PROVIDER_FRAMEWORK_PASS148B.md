# Pass 148B — Universal Import Provider Framework

Havenwild imports source material through capability-based providers and normalizes every result into the universal asset-pack contract. Providers are not tied to terrain or LPC.

## Initial providers

- Raw image sheet: slices PNG sheets into manual assets without inventing semantics.
- JSON sidecar/native pack: imports reviewed metadata into the same pack model.
- Tiled TSX: imports atlas geometry and preserves Tiled tile IDs; Wang-set presence advances readiness.
- Audio folder: registers audio files through the same pack result.
- Sprite animation sheet: slices frames while requiring a profile for clips, directions, timing, and anchors.

## Import states

`detected`, `manual_only`, `partially_configured`, `runtime_ready`, `production_verified`, `reference_only`, and `rejected` are separate states. Runtime readiness does not imply licensing approval.

## Provider contract

Every provider implements capability detection, non-destructive inspection, and normalized import. The output always contains an `AssetPackManifest`, diagnostics, state, and optional reusable profiles.

## Raw-sheet rule

A raw sheet is immediately available as manually selectable cells. Semantic IDs, terrain patterns, object behavior, animation clips, collision, and production approval are not inferred silently.

## Tiled rule

TSX is the first metadata-rich interchange path. Pass 148B establishes source geometry and Wang-set detection. Full Wang color/edge/corner, animation, probability, custom property, and collision normalization continues in category-contract work.
