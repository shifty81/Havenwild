# Pass 136 — Character Creation Foundation

This pass promotes the first canonical Havenwild character-creation contract.

## Locked behavior

- Initial creation is appearance-first: body, head, hair, eyebrows, facial hair, eyes, and color ramps.
- Only a deliberately small set of ordinary tops, bottoms, and shoes appears at creation.
- Armor, weapons, shields, advanced outfits, and most equipment are progression content acquired after play begins.
- Character content uses stable asset-role identifiers instead of hard-coded atlas coordinates.
- Runtime promotion requires `idle_down`, `idle_up`, `idle_left`, `idle_right`, and `walk_8dir` aliases.
- Side-facing idle artwork must be neutralized during asset promotion; an idle frame may not inherit the one-foot-forward silhouette from a walk frame.

## Added

- `crates/haven_assets/src/character_creation.rs`
- `content/characters/character_creation_catalog_v0_1.json`
- `tools/automation/validation/checks/characters/Validate-CharacterCreationFoundationV136.py`

## Next pass

Build the source-library promotion catalog that maps every approved body, head, hairstyle, eyebrow, facial-hair, clothing, and animation source into canonical Havenwild asset roles, then wire the creator preview compositor to those roles.
