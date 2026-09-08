# Havenwild W57K10A–W60 Unified Authoring Authority

This checkpoint normalizes the native editor around one principle:

> The canvas is a document surface. The selected layer determines the data context; the explicitly selected tool determines what a click does.

## W57K10A — editor UI authority

- The Windows UI font is initialized before the first visible editor frame.
- Startup remains on one loading surface until project, registries, document surfaces, atlases and workspace restoration are ready.
- Workspace switching and returning from Play no longer recreate the font atlas.
- Every editor text draw reasserts the default UI material to prevent custom canvas materials from leaking into text and producing black glyphs.

## W57K10 — starter cottage certification pilot

The Estate starter cottage remains the canonical certification house. Its front-gable base now uses exact left/repeat/right siding slices so the exterior edge treatment survives into the eave/gable junction. Building Composite Pixel Studio authoring is the visual correction path rather than accumulating cottage-only hard-coded offsets.

## W57K11 — two-story Estate typology

`havenwild.estate.house_two_story_upgrade` is the canonical two-story recipe candidate. It reuses BuildingRecipe/PublishedWorldAsset authority, keeps the ground floor open for living/cooking/crafting/gathering, moves the bedroom/private storage upstairs and connects levels with a reversible authored stair. Activation as the player's upgrade remains gated by visual acceptance rather than introducing a second house renderer.

## W58 — shared layer rail and tool rack

Every editable workspace receives the common Canvas Layer Rail in the upper-left of its canvas and a narrow common Tool Rack immediately beside it. Resource selection changes the resource/context only. It does not silently arm Paint or Place. Escape returns destructive workspace tools to the non-destructive Select/Inspect state.

## W58A — explicit Pixel Studio scopes

Scene context actions distinguish shared source, cell/instance variant, selected region, building composite and complete scene chunk. Multi-tile selections open as their exact 32px-per-cell composite and can be edited continuously across tile boundaries.

## W58B — authored transition/junction variants

A multi-cell authored Pixel Studio save produces a versioned local junction candidate in `content/terrain/authored_junction_variants_v1.json` while preserving the underlying terrain semantic grid. New junctions are local by default; PCG reuse requires explicit promotion to Variant or Exemplar.

## W58C — precision collision authoring

Pixel region/composite documents include an independent Collision Mask layer. Authoring resolution is 1px, the normal snap is 8px, and 32/16/8/4/2/1px precision is part of the contract. Runtime collision should compile the mask to merged rectangles/contours rather than one physics body per authored pixel.

## W59 — Authoring ChangeSets

Accepted local authoring outputs are recorded in `WORKSPACE/authoring/changesets/current/manifest.json` with target, scope, revision and output paths. Project Control Center command 63 packages those deltas into an uploadable ZIP so local hand-authoring and patch development can be reconciled deterministically.

## W60 — World Route Graph

World Routes is no longer an alternate terrain editor. Its center workspace is a synchronized split: overworld spatial map on the left and a scene-card/yarn-board graph on the right. Existing scene transitions are rendered as links. The common Link tool is the authority for future interactive graph linking.

## Locked downstream direction

- Starter cottage: single-story certification house.
- Estate upgrade: modular two-story house, open ground floor, bedroom upstairs.
- Player home customization reuses the same modular building/document/layer/change-set contracts.
- Hand-authored tiles, transitions, buildings and collision remain derived/versioned and can be promoted into PCG variants/exemplars instead of flattening generated semantic world authority.
- Future Open2D/Cortex integration should consume the generic ToolRegistry, CanvasLayerStack, scoped Pixel authoring and AuthoringChangeSet contracts rather than automating Havenwild-specific UI clicks.
