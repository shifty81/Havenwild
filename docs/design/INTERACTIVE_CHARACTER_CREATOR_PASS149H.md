# Pass 149H — Interactive Character Creator and Neutral Base Bodies

This pass replaces the fixed pre-clothed creator provider with a persistent layered starter appearance model.

## Creator surface

- Focusable name field with character input, Backspace, visible caret, 28-character cap, and nonblank validation.
- Male and female neutral base-body metadata variants. The base has no clothing baked into it and carries no explicit anatomical detail.
- Male starter outfit: T-shirt, pants, boots.
- Female starter choices: long shirt with pants, or shirt with skirt, with shoes.
- Independent skin, shirt, bottom, and footwear palette cycling.
- Only starter garments are exposed in creation. Advanced clothing, armor, tools, weapons, and accessories remain gameplay acquisitions.

## Persistence

The saved `CharacterAppearance` contains stable layer references for:

1. `body/base`
2. `clothing/torso`
3. `clothing/legs`
4. `clothing/feet`

Each layer records a stable pack/category/asset/source/variant reference plus palette and RGBA tint. Existing profiles are interpreted when possible and default safely when they predate the starter appearance contract.

## Preview boundary

The frontend now renders a layered neutral-body/starter-clothing preview directly from the appearance metadata. Production LPC sprite-sheet composition for every runtime animation remains a separate asset-generation/runtime-compositor step; this pass does not falsely flatten recolored starter layers into a new animation atlas.
