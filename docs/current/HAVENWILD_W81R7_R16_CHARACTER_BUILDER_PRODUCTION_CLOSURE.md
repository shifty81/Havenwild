# W81R7-R16 — Character Builder Production Closure

This ten-pass block closes the gap between the Universal LPC source model and Havenwild's editor/game character workflows.

## Authority

`sheet_definitions` are the character-item authority. A definition may own multiple layers, body-specific paths, exact `zPos`, variants, tags/dependencies, standard actions, custom 128/192px actions, recolors and provenance. Raw PNG credit records remain useful for diagnostics/attribution lookup but are not independent wardrobe items.

The shared flow is:

`Universal LPC sheet definition -> UniversalLpcCharacterBuilderCatalog -> UniversalLpcCharacterRecipe -> UniversalLpcCharacterResolver -> editor/game/NPC/runtime`.

## R7 — Exact definition and zPos

Stable definition IDs are derived from the relative sheet-definition path. Character Studio assembly uses `UniversalLpcCharacterResolver`; it no longer guesses a global body-part order for production composition. Multi-layer definitions retain exact `zPos`.

## R8 — Definition-level catalog

The Assets panel presents definition-level choices. Animation PNGs no longer appear as duplicate clothing/items. Broad creator category and exact selection group remain separate so multiple related upstream types do not overwrite one another unnecessarily.

## R9 — Identity foundations

A valid recipe always contains a locked Body and Head. Headwear is an optional overlay and cannot satisfy the Head foundation. Child, Teen, Adult and Elder identity choices select real body/head foundations. Sex and age are recipe state, not display-only labels.

## R10 — Direction and animation preview

South/West/North/East select the canonical ULPC rows. Standard actions use authored Havenwild/ULPC frame-cycle metadata. Custom actions retain 128px/192px source-frame envelopes and the character preview centers 64px body/clothing layers within those larger action canvases.

## R11 — Creator UX

Normal Character Studio is a character builder: Identity, direct Wardrobe category selection, definition choices in Assets, lock/add/remove, scoped Appearance/Outfit/All randomization, direction/action playback, save/load/publish. Raw paths/license/source diagnostics remain under Advanced/Properties.

## R12 — Game creator

The actual game character creator carries the same typed recipe and exposes the same builder category/definition authority. Persisted profiles retain the recipe in the existing `characterRecipe` field.

## R13 — NPC generation

NPC generation creates the same typed recipe and uses the same deterministic definition-level wardrobe catalog. NPCs do not maintain a separate sprite vocabulary.

## R14 — Equipment/custom actions

Weapons, off-hand and tools are typed equipment selections. A custom action's background/foreground sheets participate only in that custom action. The remainder of the character uses an explicit standard companion motion for the same action, avoiding detached equipment or custom-layer leakage into Idle/Walk.

## R15 — persistence/provenance

Selections retain item ID, variant, definition source, selected license, complete license set, source URLs and ShareAlike requirement. The recipe retains the pinned Universal LPC source commit.

## R16 — production certification

Character Studio, player creation, NPC generation and typed runtime loading must all point at the same builder/recipe/resolver authority. Legacy appearance profiles remain loadable for compatibility, but a typed recipe is preferred when one exists and must fail closed if its required foundation cannot resolve.

## Visual acceptance

Test Male/Female across Child/Teen/Adult/Elder. Randomize Appearance, Outfit and All repeatedly. A head must always exist under headwear. Boots/pants/torso/headwear must retain definition z-order. Rotate all four directions. Test Idle, Walk, Run, Slash and Thrust. Equip an axe/hammer/rod/whip and verify custom action layers do not appear during unrelated standard actions.
