# Havenwild W54E — Starter Cottage Production Layout

The first trustworthy W54D2 Estate screenshots proved that routing was fixed, but the development starter cottage itself was not production-shaped. Exterior scale was too small, the flat-shingle nine-slice read as tall rectangular roof panels, and entering the house exposed only a small floor patch because the camera-local cutaway removed the only visible wall shell.

W54E replaces that recipe with an 8×6 same-world BuildingInstance while preserving the Estate route-aligned front-door world tile `[59,34]`.

## Room program

- **Bedroom** — bed plus personal storage.
- **Living / Crafting / Cooking** — work table, chair, cast-iron hearth/cooking station and storage.
- One interior doorway connects the two rooms; no scene transition is introduced.

## Wall presentation

The south/front façade now uses the exact W54D1-reviewed cream `Siding, Plain` left/repeat/right strips. North/east/west exterior facings remain logical and fail-closed until exact facing-specific art is proven. Inside, a rear interior finish and blocking room divider remain visible because only the front façade and roof belong to camera-local cutaway groups.

## Roof presentation

The flat brown nine-slice is retired from the starter cottage. W54E publishes one intact exact brown hipped-roof authored module from `Structure/Roofing/Hipped Shingle Roof A.png` and places two modules as west/east bays. The source envelope is not scaled, mirrored or split into guessed hip/valley cells.

## Architecture

BuildingRecipe now supports a list of authored roof-module placements. Roof materialization and roof-specific structural validation were moved into `building_recipe/roof.rs`, keeping the main `building_recipe.rs` module below Havenwild's 750-line ceiling.
