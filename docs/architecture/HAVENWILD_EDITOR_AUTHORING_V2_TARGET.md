# Havenwild Editor Authoring V2 — Target Contract

This document is the concise target extracted from HW-EDITOR-AUDIT-01. It is intentionally behavior-neutral.

## One authoring kernel

Native Editor, F3 Runtime Edit, PIE and automation are frontends over shared `haven_authoring` commands/transactions. A frontend may expose fewer capabilities, but it may not invent a second data model for the same operation.

## One Game Canvas

World, Scene, Scene Library, Routes and UI are contextual views/documents inside Game Canvas. The creator-facing shell is GameMaker/LDtk-like: left tool rail, central live canvas, contextual Assets/Outliner/Inspector, collapsible Layers/Output/Validation.

## Permanent manual construction

Semantic/autotile paint and exact source-atlas placement coexist. Raw atlas tile/region selection can be placed directly, rotated/mirrored when metadata permits, and stored as a manual override. A selected arrangement can be promoted to a stamp/prefab/structural pattern/PCG exemplar.

## Typed assets and layers

Source sheets are containers. Normal palettes expose semantic/runtime assets. Each asset declares its semantic layer, source region(s), pivot/anchor, footprint, collision/interaction, animation, orientation rules, provenance and runtime/editor readiness. Filename substring guessing cannot be normal authority.

## Spawn authoring

Spawn is a first-class Game Canvas tool with typed anchors for Player Start, Play From Here, NPC, population spawner, animal, resource, encounter, transition destination and PCG anchor.

## F3 contract

F3 toggles a lightweight in-game developer overlay. It does not automatically enter world-edit/build mode. Runtime Edit is opened explicitly. Diagnostics are cached and visibility-driven; drawing the overlay must not repeatedly load/parse catalogs from disk.

## Parity contract

Equivalent actions from Native Editor, Runtime Edit and automation resolve to the same stable asset IDs, authoring command, coordinates, layer semantics, validation, persistence and PIE result. UI parity is not required; operation/data parity is.
