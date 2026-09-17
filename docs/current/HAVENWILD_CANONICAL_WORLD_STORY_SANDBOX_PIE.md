# Havenwild canonical Base World, Story/Sandbox, and native PIE convergence

Date: 2026-09-17. Status: **active implementation contract, not a claim that PIE or client Base-World instancing is complete**.
Baseline: September 17 `Passmanual` source rollups; preserve existing Havenwild PCC and Rust/Macroquad architecture.

## Product decision

- There is **one project-owned canonical Havenwild Base World**. Its authored regions, Willowmere core, required cities, roads, quest anchors, landmark entrances and approved art/asset definitions are built and certified once in the native Game Canvas.
- The editor opens **the Base World** as its editing source. It does not choose a random seed, present player New World menus, or treat the nine-scene `GameWorld::starter()` compatibility fixture as published world authority.
- Gameplay modes do not own worlds. **Story** consumes the authored storyline with default rules. **Sandbox** consumes the *same* storyline and can customize permitted rules and generation parameters; it does not duplicate scenes, quests, NPC registries or town definitions.
- The client's New World produces a new per-player instance from Base World revision + validated options + seed. Gameplay changes write to that instance only. Editor changes must never be applied to a player's existing save by silently regenerating it.
- The editor Game Canvas draws from the same authoritative visual plans/assets as the game. **Actual PIE** means the real gameplay simulation runs inside that editor canvas, accepting game input, with a Stop transition that restores authoring state. A second executable or external game window is **external Play**, not PIE.

## Ownership and precedence

| Data | Owner | Allowed mutation |
|---|---|---|
| Canonical Base World + authored scenes + authored-override masks + identity/version | Project and native authoring editor | Explicit authored save/publish only |
| Story content: dialogue, quest graph, NPC identities, required landmarks and entrances | Shared authored content | Explicit editor content edit |
| Mode profile: Story or Sandbox and allowed gameplay modifiers | Shared gameplay settings/validator | New World selection or explicit instance rule change |
| World variation: seed and semantic generation modifiers | Existing `WorldCreationSettings` and existing generator | Only whitelisted procedural space, after structural validation |
| Play session: transient player/world state | PIE runtime session | Disposable on Stop unless explicit authoring promotion exists |
| Player instance save: generated state and player mutations | Game save/persistence | Gameplay actions and compatible migration only |

Never encode gameplay mode in `WorldDifficultyPreset`: its existing `Story` variant is a difficulty preset and must remain distinguishable from the future **Story gameplay mode**. Use the existing settings and world generator; introduce one small mode-profile field only when both game client and persistence are ready to consume it. Do not add an unused alternate generator or another world registry.

## Required first implementation gates

### Gate B0: recover/create the real canonical source

The existing `content/worldgen/dev_worlds/core_dev_001/README.md` declares a source-controlled mirror `world.tworld`, but that file is **not in the 2026-09-17 source rollup**; `WORKSPACE/saves` is omitted too. Before publishing the Base World, the code must explicitly load a valid authored source or provision a deterministic **production** baseline through the existing generator. It must not silently publish `EditorWorldModel::starter()` into the source-controlled mirror. A missing Base World is a distinct state from a corrupt existing world; report both. The developer has explicitly permitted discarding the current visual test saves, but no silent overwrite of a different detected world identity or corrupted source is permitted.

### Gate E0: reach the editable canvas

Scene Library is a navigator, not a prerequisite to using the Game Canvas. Scene cards and outliner rows directly open through the existing `ensure_selected_scene_document_open` path. The library canvas input is never gated by right dock visibility. An inspector is optional; a card has a visible Open/Edit affordance. World Overview must offer one explicit Edit Region action. Fixture scenes must be marked as fixtures rather than misrepresented as the Base World.

### Gate B1: single save + reload revision

The current Save All writes the local `WORKSPACE/saves` copy; the live reload path refers to `content/worldgen/dev_worlds/core_dev_001/world.tworld`. Converge these with one reviewed publish transaction, one revision/identity and a round-trip check before emitting live reload. Prevent two competing canonical sources and keep player saves separate.

### Gate PIE1: actual in-canvas runtime, not external launch

Refactor the currently executable-owned game loop into a reusable host-independent session **incrementally**; retain the game executable and external Play until integration is certified. The host must supply viewport/render context, input ownership, session world clone/overlay, controlled tick and draw, audio routing, dev diagnostics and explicit Stop. Never start a second Macroquad event loop inside the editor or embed an external HWND and call it PIE. On Stop, release gameplay input and preserve editor selection, camera, authoring undo, unsaved edits and original Base World state. Play mutations cannot publish to Base World without explicit review.

### Gate Mode1: Story and Sandbox from one world

Both modes load the same Base World revision and story assets. Story uses authored/default narrative conditions and locked critical geometry. Sandbox may change approved survival/economy/build/PCG settings while keeping the story available. Every option declares an allowed target set and constraints; generation must preserve Willowmere, required quest anchors, all mandatory travel connections and authored overrides. Reject conflicting combinations before New World creation. Persist profile identifier, settings, seed and Base World version in the instance metadata for deterministic reopen/migration. Existing saves without a mode value get an explicit compatibility default; never silently reinterpret their world geometry.

## Current state after E0 first source pass

The accompanying first implementation patch repairs **Scene Library navigation only**: visible Open/Edit on card, direct card and list open, canvas clicks independent of the right dock, inspector actions restricted to visible Properties, and corrected inspector geometry. This does **not** implement canonical world generation, Base World publication, gameplay mode selection or PIE. Those remain subsequent gates. Run the next Windows PCC Full Gate once a coherent milestone batch is complete; verify actual UI interactions manually.

## Acceptance scenario

1. Launch editor: visible Base World identity; no unexplained starter replacement or generator selection.
2. Select Willowmere region or a registered interior; Open/Edit enters actual canvas directly with or without docks.
3. Author a visible object or terrain edit, Save, reload and verify editor/client parity on identical authored data.
4. Press Play in the canvas. Real game simulation ticks; player moves/uses tools/interacts. Stop returns to same editor view without world/save leakage.
5. Start Story and Sandbox client instances of the *same* Base World; story quest anchors match and permitted settings vary only eligible procedural content.
6. Reopen both instance saves; Base World and other instances remain unchanged.

## Deferred in this implementation patch

No new generation settings UI; no separate sandbox-scene assets; no ForgePY/PCC replacement; no fake PIE; no new visual/cliff resolver; no deletion of compatibility scenes or licensed artwork.

## Implementation update: B02 canonical authored world bootstrap (September 17)

Source work now provides a checked-in development descriptor, shared `haven_world::materialize_base_world` for editor initial generation and client New World terrain generation, one editor source path, direct scene-open UI, source-first validated Save/replica publication, and external development launch from the authored source. The editor uses the checked-in scene-rectangle layout and does not reroll geography during ordinary editor startup. Legacy starter scene fixtures are not installed into the generated Base World. Loading an unreadable existing Base World fails visibly; save/play is blocked. There is **no pre-generated world.tworld shipped in this patch**: editor first-run generation creates it locally, then it must be explicitly included in a later authored-world source handoff/commit. The game client still does not layer authored source overrides onto arbitrary Story/Sandbox new-world variations. **Genuine in-canvas PIE is not implemented**: existing Play launches the external development client. These source changes require the Windows PCC Full Gate and a manual editor/client acceptance run before certification.
