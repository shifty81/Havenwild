# Project Rollup Audit - 2026-05-25 (Night Drop)

## Summary

These root archives were audited during the architecture restructure pass:

1. `havenwild_project_rollup_20260525.zip`
2. `havenwild_project_rollup_20260525_v2.zip`
3. `HAVENWILD_PROJECT_SOURCE_OF_TRUTH_REGENERATED.zip`
4. `HAVENWILD_PROJECT_SOURCE_OF_TRUTH_REGENERATED.md`

## Result

- The **focused packs** (`scene rectangles v008`, `editor systems v009`, `character animation contract v010`) were the best immediate implementation targets.
- The two rollup zips were treated as **archival/handoff material**, not as direct repo overlays.
- The regenerated source-of-truth markdown was promoted into:

```text
docs/design/hearth-and-hollow-project-source-of-truth-2026-05-25.md
```

## Applied from this audit

- Soft architecture split inside the existing Rust workspace:
  - `haven_core::scene_rectangles`
  - `haven_core::animation_contract`
  - `haven_editor::command_bus`
  - `haven_editor::project_file`
  - `haven_editor::validation_registry`
- New content-backed contract files staged under:
  - `content/worldgen`
  - `content/editor`
  - `content/animation`
  - `content/schemas`
- Imported architecture/spec docs staged under:
  - `docs/engineering/imported/scene-rectangles-v008`
  - `docs/engineering/imported/editor-systems-v009`
  - `docs/engineering/imported/character-animation-v010`

## Not treated as direct overlays

- Legacy or mixed source trees embedded inside the rollups.
- Broad future architecture proposals that exceed a safe one-pass refactor, including full `haven_*` crate renaming/splitting, networking, save-service extraction, and full web/pixel editor implementation.

## Current architecture direction

The repo now carries the incoming architecture contracts in active source form without pretending the entire future multi-crate Havenwild platform is already complete. The current pass establishes the contract/validation/project-shell layer first, which is the safe bridge from the existing `tavern_*` prototype to the future `haven_*` architecture.
