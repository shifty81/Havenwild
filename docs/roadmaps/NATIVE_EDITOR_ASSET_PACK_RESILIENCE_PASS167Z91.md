# Havenwild Native Editor Asset-Pack Resilience — Pass167Z91

## Purpose

Pass167Z91 closes the single workspace-test failure reported after Pass167Z90 and strengthens the native editor's asset-catalog authority before continuous Alderreach world editing begins.

The failed assertion expected the promoted OGA LPC cliff ladder to appear under **Elevation & Cliffs**. The cliff pack, ladder manifest entry, source sheet, category mapping, and license record were all present. The failure occurred because strict asset-pack discovery treats any invalid optional pack under `user/asset_packs` or `mods/asset_packs` as a project-wide error. Catalog loaders then discarded all successfully mounted built-in packs and fell back to the legacy pond-only stamp registry.

## Discovery lanes

Two explicit discovery policies now coexist:

- `RuntimeAssetSession::discover` remains strict for certification, packaging smoke tests, and callers that must reject every invalid production configuration.
- `RuntimeAssetSession::discover_tolerant` mounts every valid production pack, preserves the full discovery report, and exposes invalid optional-pack diagnostics without hiding Havenwild's built-in assets.

The tolerant lane is used by the native editor catalog, editor texture/stamp loading, the default stamp registry, and game-runtime recovery after a strict-discovery failure.

## Native editor visibility

The Imports bottom panel now reports:

- Mounted production-pack count.
- Diagnostic failure count.
- Stable source-binding count.
- Runtime-ready palette count.
- Intake and reload state.

A broken optional pack therefore remains visible as a diagnostic rather than silently removing cliffs, ramps, ladders, bridges, cave attachments, or other valid providers from the editor.

## Regression coverage

A dedicated unit test builds a temporary project containing one valid built-in pack and one malformed optional user pack. Strict discovery must reject the project; tolerant discovery must still mount the valid pack, retain one failure diagnostic, and build its stable source cache.

The existing asset-palette regression remains unchanged in intent: the OGA LPC cliff ladder must be present under **Elevation & Cliffs**.

## Acceptance

The Windows workstation must rerun Build All through all workspace tests. After this gate is clean, the next feature pass is the continuous Alderreach World Editor: one global surface canvas with partitions treated only as optional diagnostics.
