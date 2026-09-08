# Havenwild Pass 167V — Universal LPC Character and NPC Authority

## Source audited

- Repository: `liberatedpixelcup/Universal-LPC-Spritesheet-Character-Generator`
- Source snapshot: `0f898bb675a1abe16ce430e82e3bf9daed278690`
- Uploaded archive SHA-256: `7a6ea376d41090b87182b669c74d5b6832ece92595da290b8f73f49e7fb432fc`
- Archive entries: 95,742
- Actual spritesheet files: 88,235
- Sheet-definition JSON files: 883
- Credited source records: 13,818

The repository is treated as a local authoring dependency. It is not copied into every incremental patch or complete source checkout.

## Commercial-use audit

Every credited source record has at least one selectable non-GPL commercial license in the uploaded snapshot:

- Preferred commercial tier: 11,780 records
- Conditional ShareAlike tier: 2,038 records
- GPL-only or unresolved records selected for production: 0

Preferred selection order is CC0, OGA-BY, then CC-BY. CC-BY-SA is retained in a conditional pool and requires compliant attribution and derivative-art redistribution. A license is chosen per source record; no asset is approved merely because it appears in the generator.

## Havenwild identity rules

- Sex values: Male, Female
- Age groups: Child, Teen, Adult, Elder
- Muscular and Pregnant are morphology or life-state variants, not sex values.
- Elder characters use the reviewed adult Male/Female body geometry with elderly-compatible heads, eyes, noses, hair, and facial layers until a dedicated elder base is approved.
- Player creation launches with Human characters and a curated component pool.
- Fantastical, undead, lizard, wing, tail, skeleton, zombie, and corruption content remains available for controlled NPC, distant-island, ruin, and monster profiles.

## Source coverage

The source contains large component families for body, head, eyes, hair, facial detail, hats, torso clothing, dresses, arms, shoulders, neck accessories, legs, footwear, backpacks, capes, tools, weapons, shields, tails, wings, prostheses, and mobility aids.

Advertised body animation families include spellcast, thrust, walk, slash, shoot, hurt, watering, idle, jump, run, sit, emote, climb, combat, one-handed slash, backslash, and halfslash. Actual component readiness still varies; compatibility checks must reject incomplete combinations.

## Normalized ownership

`CharacterRecipe` remains the saved identity authority. Composed PNG sheets are cache outputs.

The correct flow is:

```text
Universal LPC source + sheet definitions + credits
→ commercial/license filter
→ compatibility catalog
→ CharacterRecipe
→ source-native compositor cache
→ Character Creator / Character Select / Character Studio / runtime / NPCs
```

The pipeline forbids blind 64×64 or 64×96 cropping, filename guessing, and using the first walk frame as a neutral idle.

## NPC generation

Initial generation profiles cover Willowmere residents, farmers, merchants, craftspeople, coastal populations, distant-island peoples, and ruins inhabitants. Authored NPCs keep fixed identities; profiles generate supporting populations and outfit variants.

Outfits are contextual layers rather than permanent identity:

- everyday
- work
- sleep
- formal
- rain
- winter
- travel
- festival
- combat
- uniform

## Character Studio and Pixel Studio

Character Studio owns component filtering, recipe creation, NPC generation, compatibility, and licensing. Pixel Studio edits an individual selected source layer through a Havenwild-owned override. Saving an override invalidates only affected composite caches and refreshes characters using those recipes in editor/runtime previews.

## Local bootstrap

```bat
set HAVENWILD_ULPC_ARCHIVE=C:\path\Universal-LPC-Spritesheet-Character-Generator-master.zip
tools\automation\characters\Bootstrap-UniversalLpcGenerator.cmd
```

This validates the archive, extracts it into `.local/dependencies`, mounts it at `assets/source/licensed/universal_lpc_generator`, and generates the local character authority under `WORKSPACE/generated`.

## Next implementation boundary

The next pass should wire the generated authority into the live Character Studio catalog and compositor, then replace the narrow 194-component creator view with filtered source-backed queries while preserving old saves and fallback assets.
