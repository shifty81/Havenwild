# Havenwild Editor Authoring V2 — Target Contract

Updated by `HW-EDITOR-GAP-AUDIT-02`. This supersedes the workflow wording from HW-EDITOR-AUDIT-01 without changing runtime behavior.

## One authoring kernel

Native Editor, F3 Runtime Edit, PIE and automation are frontends over shared `haven_authoring` commands/transactions. A frontend may expose fewer capabilities, but it may not invent a second data model for the same operation.

## One Game Canvas

World, Scene, Scene Library, Routes and UI are contextual views/documents inside Game Canvas. The creator-facing shell is GameMaker/LDtk-like in workflow: central live canvas, contextual layer palette/toolbox, Assets/Outliner/Inspector, and collapsible Layers/Output/Validation.

## Layer -> palette -> tool -> inspector

The active layer determines the contextual palette and valid tools. `Place` is the generic placement operation for compatible Assets, Entity Definitions and Prefabs. Ordinary content types do not receive bespoke placement windows.

## Spawn placement is normal entity placement

There is **no separate Spawn tool or Spawn UI**. `Player Start`, NPCs, animals, spawners and other authored runtime markers are Entity Definitions available from the Entities/Gameplay palettes and placed with the standard Place workflow. A Player Start definition can enforce a unique-instance constraint.

`Play From Here` is an ephemeral development launch command available from the Play controls/context menu. It is distinct from the persisted `Set Player Start Here` operation.

## Permanent manual construction

Semantic/autotile paint and exact source-atlas placement coexist. Raw atlas tile/region selection can be placed directly, transformed when metadata permits, and stored as a manual override. A selected arrangement may be promoted to a Brush, Prefab or PCG Exemplar.

## Typed definitions and instances

Source sheets are containers. TileSets expose stable slices/tiles. Materials define semantic terrain/structure painting. Entity Definitions and Prefabs define reusable content. Instances contain placement state and permitted overrides. Filename substring guessing cannot be normal semantic authority.

## Terrain without name-specific rules

Grass, water, pond, sand, dirt, road and future Materials use the same metadata/rule contracts. The editor supports Connect, Path and Exact/Manual placement modes plus normal fill/rectangle/replace/pick operations. Specialized gameplay behavior belongs in typed metadata/capabilities, not material-name conditionals.

## F3 contract

F3 toggles a lightweight in-game developer overlay. It does not automatically enter world-edit/build mode. Runtime Edit is opened explicitly. Diagnostics are cached and visibility-driven; drawing the overlay must not repeatedly load/parse catalogs, rebuild complete-world indexes or scan broad off-screen content.

## Parity contract

Equivalent actions from Native Editor, Runtime Edit and automation resolve to the same stable asset/definition IDs, authoring command, coordinates, layer semantics, validation, persistence and PIE result. UI parity is not required; operation, data and rendered-content authority parity are.

See `docs/architecture/HAVENWILD_GAME_CANVAS_WORKFLOW_V2.md` and `_audit/EDITOR_WORKFLOW_GAP_AUDIT_02.md`.
