# Havenwild Terrain Tile + Variant Authoring — A14AB

## Goal

Turn the terrain work Havenwild already owns into one professional resource workflow without replacing the semantic terrain, LPC/V7 atlas, tuple resolver, Pixel Studio, Asset Intake, or PCG authorities.

The player/editor-facing rule is simple:

> Paint semantic terrain. Author visuals as reusable terrain resources. Never make world cells depend on raw atlas coordinates.

## Existing authorities retained

- `TerrainMetadata` remains the semantic terrain contract: terrain set/id, match mode, eight peer assignments, movement, collision, footsteps, seasons, and PCG tags.
- The existing exact terrain tuple/pattern resolvers remain responsible for topology.
- The existing read-only LPC/ElizaWy/Tiled source mounts remain immutable upstream sources.
- Pixel Studio remains the visual repair/authoring surface and produces project-owned outputs.
- Asset Intake / existing certification remains the promotion authority. A14AB does not invent another certification vocabulary.
- Manual authoring and PCG must consume the same promoted terrain resources.

## Professional authoring model

### 1. Semantic family first

A tile belongs to a semantic terrain family such as Grass, Sand, Road, Stone Path, Shallow Water, or Mountain Rock. Its gameplay meaning is not duplicated into every visual variation.

### 2. Four intake paths

The complete workflow should expose:

1. **New Tile** — create a blank 32x32 project-owned tile inheriting the active terrain family.
2. **Create Variant** — non-destructively clone the selected resolved tile into a project-owned Pixel Studio draft.
3. **Atlas Slice** — promote an exact rectangle from an imported/project sheet through the existing Asset Intake path.
4. **Tiled/TSX Terrain Import** — reuse the existing importer for Wang/terrain peers, probability, collision, and animation metadata.

A14AB implements the first two directly in the Canvas Palette and retains the existing intake/import foundations for the latter two.

### 3. Variant inheritance

A derived visual variant inherits by default:

- semantic terrain identity;
- terrain topology/pattern assignment;
- gameplay/collision/movement/footstep properties;
- provenance/license lineage;
- PCG tags.

Only the visual pixels and explicit variant controls should differ until the author deliberately detaches a property. This avoids the metadata drift common to systems where each alternative must be configured from scratch.

### 4. Automatic probability

Each eligible variant has an automatic selection weight.

- `weight > 0`: eligible for deterministic automatic selection after topology is resolved.
- `weight == 0`: manual-only but remains terrain-aware, so neighboring autotile resolution still understands its semantic family.

Topology score always wins before weight. Weight only chooses among equally valid visual candidates.

### 5. Transform policy

Flip/rotation generation must be opt-in per terrain family/variant. Havenwild defaults to no transforms and prefers untransformed source art because top-down lighting, shadows, cliff direction, and water flow often make arbitrary transforms visually invalid.

### 6. Coverage

The Palette exposes a **Coverage** action into the existing W77 terrain authoring lab/repair system. The final coverage surface should show:

- required patterns;
- covered patterns;
- missing/unsupported patterns;
- candidate count/weights for each pattern;
- exact source cell(s);
- partition-seam and world-wrap fixtures;
- 3x3/5x5 randomized variant previews;
- water/contact animation fixtures where relevant.

Clicking a missing pattern should open the existing Pixel Studio repair document rather than inventing a second tile editor.

### 7. Draft → review → production

A14AB terrain drafts are project-owned and start as `Draft`, `pcgApproved=false`.

Promotion must remain explicit:

`Draft visual → validate provenance/topology/coverage → existing approval authority → optional PCG approval → production resolver`

No draft becomes a PCG resource merely because it was saved.

## Canvas Palette UX

When a terrain-compatible brush is active, the bottom Canvas Palette exposes:

`+ Tile | Variant | Coverage`

- `+ Tile` creates a blank project-owned tile draft for the current semantic family.
- `Variant` requires a selected Palette resource and opens an immutable-source-derived working copy in Pixel Studio.
- `Coverage` opens/reveals the existing terrain coverage/repair workflow.

The selected world/terrain context is preserved when Pixel Studio opens.

## Draft persistence

Draft metadata uses `havenwild.terrain_variant_draft.v1` and records:

- stable draft id;
- origin kind;
- parent resource for variants;
- semantic terrain family/set;
- topology match mode;
- immutable source path and region;
- project-owned output path;
- deterministic variant weight;
- inheritance policy;
- transform policy;
- promotion state and PCG approval.

Working draft records live under `.local/editor/terrain_variant_drafts/`. Published pixels live only under `assets/source/original/`.

## Next production closure (A14AC+)

1. Bind promoted drafts into the existing asset-pack `variants` lane instead of treating one `TileKind` as one visual binding.
2. Expose variant weight/transform controls in Properties.
3. Build the full Patterns/Coverage matrix from the exact resolver rather than the current lab-only jump.
4. Add dependency preview before modifying/promoting a variant used by manual maps or PCG.
5. Add seasonal-variant inheritance and batch derivation.
6. Make the Project Asset Browser show `Base + N variants`, weights, topology coverage, provenance, certification, and PCG status on resolved cards.
7. Allow safe re-parenting/detach of a visual variant while preserving stable resource IDs.
8. Add fixture-based frequency tests so deterministic weights remain stable across saves/builds.
