# HW-AUTHORITY-10 — Shared Authoring Spine

Completes AUTH-06 through AUTH-10 without replacing existing editor surfaces or domain owners.

- AUTH-06: canonical `WorkspaceId` with GameCanvas, Assets, Pixel, Animation, Character, reserved/unavailable Data, Logic, Sound. Existing `EditorViewportMode` remains compatibility routing during migration.
- AUTH-07: `GameCanvasView` makes World, Scene, Scene Library, Routes and UI contextual Game Canvas views.
- AUTH-08: read-oriented `AuthoringSession` and `EditorContextSnapshot` connect document, workspace/view, selection envelope, layer, UniversalTool, palette, edit scope and runtime state without absorbing domain data.
- AUTH-09: existing `CanvasLayerDescriptor` gains generated/derived/diagnostic/writable authority flags. Existing `UniversalTool` remains canonical; `ToolAvailability` provides an explicit disabled reason rather than silent fallback.
- AUTH-10: `PaletteProviderId` provides contextual Terrain/Structure/Pixel/Character/Animation/UI routing while the existing shared Palette UI remains the presentation surface.

This pass intentionally does not add a second Tool Rail, Layers panel, Palette, Pixel implementation, global World/Scene/PCG studio, document god registry, or Cortex-specific mutation path.

The next checkpoint consumes this spine for Assets V1 and composition/provenance work.
