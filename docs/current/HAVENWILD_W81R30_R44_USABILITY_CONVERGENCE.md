# Havenwild W81R30-R44 — Asset / Character / World / Help / NPC Usability Convergence

Status: SOURCE-CERTIFIED HANDOFF — Windows Full Quality Gate required
Baseline: Pass167Z109W81R29
Pass block: Pass167Z109W81R30R44
Date: 2026-08-26

## Purpose

R30-R44 converts the LPC/ULPC intake and existing editor foundations into connected production workflows. The block deliberately reuses Havenwild's existing CharacterRecipe/compositor, semantic CanvasWorkspace Layers, deterministic world generation/hydrology/cliff systems, Scene authority, and validator architecture instead of creating parallel systems.

## R30 — Governed asset promotion

- LPC source cards remain read-only/non-placeable until a Havenwild binding is certified.
- Finish Setup creates a governed promotion candidate rather than copying arbitrary mount content into the repository.
- Batch Setup groups the exposed source catalog by semantic family and records exceptions for review.
- Generated R30 promotion queue currently contains 320 source references across 18 semantic families.

## R31 — Character Wardrobe, Equipment Slots and semantic Layers

- Character Studio retains Create and Wardrobe & Gear as separate user-facing catalog surfaces over one CharacterRecipe authority.
- Character Layers are derived from the actual recipe rather than a duplicate editor-only list.
- Layer modes: Composition and Equipment Slots.
- Layer selection synchronizes the Wardrobe category/slot.
- Layer eye controls are preview-only visibility overrides; they do not unequip or mutate the recipe.
- Definition-driven LPC z-order remains locked and inspectable rather than freely reorderable.

## R32 — Character animation coverage

- Generated source-family coverage audit currently classifies 2,315 relevant ULPC families.
- 304 families have Walk presentation but no Run presentation in committed source metadata.
- Coverage differentiates source gaps from resolver/mapping defects so missing garments are not silently treated as unequipped.
- NPC generation filters candidates against each profile's required animation families.

## R33 — Gameplay-oriented LPC promotion

Generated catalog views map exposed LPC source families to terrain, farming, mining/forge, forestry/carpentry, tavern/interiors, settlements and effects. The current inventory reports 414 loop entries (families may participate in more than one gameplay loop).

## R34-R35 — Universal semantic Layer interaction

- World and Scene Layers are semantic edit authorities.
- Selected Layer constrains canvas editing and updates Tool Rail / Asset Browser context.
- World contexts include Terrain Materials, Derived Transitions, Structural Terrain/Cliffs, Water, Roads & Paths, Vegetation, Resources, Structures, Props, NPC/Spawn, Interactions, Collision, Lighting/FX, Logic/Regions, Authored Pixel Override and Generated/Source Reference.
- Scene contexts include local terrain/structure/furniture/props/NPC/triggers/interactions/collision/lighting/sound/FX/logic authorities.
- Generated transition/source layers remain protected.

## R36-R38 — Real Development World + production generation contract

- World Studio can frame/render the complete persistent Development World rather than only one selected island rectangle.
- Editing a different landmass transfers authoring focus to that landmass.
- Production world contract is finite Archipelago, 3-15 total major landmasses, ocean on all outer boundaries, Willowmere generated/protected first.
- Regeneration scopes: Entire World, Landmass, Region, Hydrology, Vegetation, Resources and Settlements.
- Production stages explicitly compose the existing elevation/geography, drainage/hydrology and structural/cliff authorities before terrain presentation and authored-override replay.
- Generated world regions now have seed-scoped stable region identity independent of their preview rectangle.

### Compatibility boundary

The existing scene-rectangle manifest remains a persistence/materialization compatibility adapter in this block. Legacy Scene rectangles derive the new stable production region key. R30-R44 does not claim to have removed every legacy rectangle consumer or rewritten save persistence around dynamic region IDs; it creates the guarded migration authority without destabilizing the current runtime.

## R39-R40 — Shared Pixel / transition workflow

- World and Scene pixel editing continue through the shared raster-authoring workflow.
- Semantic Layer selection determines what Pixel operations target.
- Derived transition output is not directly destructively painted.
- Unsupported terrain combinations route to the existing transition-authoring/repair workflow and publish back into the world authority.

## R41 — World / Scene convergence

- Scene Bank evolves into a Scene Browser over authoritative world scenes, buildings/interiors, caves/dungeons and generated/special scenes.
- Actions include Open in Scene Editor, Locate in World, Duplicate Scene and Validate References.
- World-assigned Scenes can locate/frame their exact World rectangle.
- Off-world interiors/caves report that status rather than inventing coordinates.
- Scene reference reporting includes stable production region identity for legacy rectangle-backed scenes.

## R42 — Searchable Help / Wiki

- Help expands from the original six hard-coded pages to 78 searchable articles.
- Manual index categories cover Getting Started, Editor, Assets, World Studio, Scene Studio, Pixel Studio, Animation Studio, Character Studio, Logic Studio, Sound Studio, Workflow and Troubleshooting.
- Contextual F1 routing follows active Studio/semantic Layer where applicable.
- A generated Help coverage registry guards all current Studio modes, CanvasLayerKind values, UniversalTool values and major workflow features.

## R43-R44 — NPC profiles, restrictions, population and profile authoring

- NPC profiles support deterministic identity and profile inheritance.
- Effective profile constraints include region, faction, wealth, season, wardrobe categories, equipment categories, required animation families, required/preferred/forbidden tags and life hooks.
- Settlement population constraints include minimum, maximum, weight, uniqueness, home requirement and workplace requirement.
- Settlement context can exclude profiles when required facilities/factions are unavailable.
- Character Studio exposes effective inherited profile rules.
- Profile Rules opens a derived draft rather than mutating a base profile.
- Derived profile variants can edit population min/max/weight and home/workplace requirements, preview-generate before save, then persist under `content/characters/npc_profiles`.

## Shared presentation / occlusion

- Character presentation resolver operates below Character Studio so Studio/player/NPC paths can share it.
- Headwear can suppress hair/ears visually while the underlying CharacterRecipe selection remains intact.
- Removing headwear restores the original hair automatically.
- Initial semantic conflicts include two-handed main-hand vs off-hand and large Back-slot conflicts.
- More sophisticated authored helmet-compatible hairstyle substitutions remain a future content/presentation refinement rather than an unsafe automatic fallback.

## Certification evidence in this source handoff

Passing local source/static checks before packaging:

- W81R18-R28 LPC ecosystem intake + exposure authority
- W81R29 live LPC catalog exposure
- W81R6 Character Builder shared authority
- W81R7-R16 Character Builder production closure
- W77 terrain presentation authority + transition workbench
- W80 Tool/Layer Rail production completion
- W81 World Terrain Authoring
- W81R30-R44 usability convergence
- Validator registry load/topological-order validation
- all `content/**/*.json` parse (783 files at handoff)
- Python automation compile check
- `git diff --check`
- conservative delimiter sanity over all changed/untracked Rust files

No Rust/Cargo toolchain exists in the packaging environment. The user's Windows Full Quality Gate is the authoritative compiler/test checkpoint.

## First visual acceptance after Full Quality Gate

1. World Studio: open Complete World and verify all persistent landmasses are visible/navigable.
2. Select Terrain, Vegetation, Resources, Structures, NPC/Spawn and Collision Layers; verify Tool Rail / Assets context changes and clicks do not mutate unrelated authorities.
3. Derived Transitions: verify direct destructive editing is blocked and transition repair is offered.
4. Scene Browser: Locate in World for a world Scene; validate an off-world interior/cave reports no world assignment.
5. Character Studio: switch Create / Wardrobe & Gear; inspect Composition / Equipment Slots; hide/show an equipped layer without unequipping it.
6. Equip headwear over visible hair; verify hair is suppressed but restored when headwear is removed.
7. Preview Walk then Run on a garment with partial coverage; verify the Layers rail reports the missing action instead of pretending the item was unequipped.
8. NPC mode: change Profile, Generate, inspect inherited effective rules, open Profile Rules, alter population constraints and preview-generate the draft.
9. Help: search `terrain`, `transition`, `helmet`, `npc profile`, `collision`, `world generation`; verify category index and contextual F1 routes.
10. Asset Browser: exercise individual Finish Setup and filtered Batch Setup; verify source-only LPC cards remain non-placeable until bound.

## Next boundary after acceptance

If the Windows quality gate and visual acceptance are green, the next development block should focus on R45 population certification and subsequent runtime/content production rather than adding another competing editor authority. The dynamic-region persistence migration can then proceed incrementally from the stable production region keys introduced here.
