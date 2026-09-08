# W81R6 — Character Builder Foundation + Shared Authority

W81R6 converts the Character Studio identity/wardrobe surface from a loose recipe browser into the front end of one shared Havenwild character-builder authority.

## Locked contracts

- `body` and `head` are mandatory foundation selections. Headwear, helmets, hair, facial details, clothing, tools and equipment are overlays and may never replace either foundation layer.
- Sex remains Male/Female. Age remains Child/Teen/Adult/Elder.
- Child selects the ULPC child body/head foundation.
- Teen selects the ULPC teen body and sex-compatible human head.
- Adult selects the sex-compatible adult body/head.
- Elder keeps the sex-compatible adult body but selects the sex-specific elderly head.
- Changing sex or age immediately rebuilds the mandatory foundation and the assembled preview.
- Clear/randomize/remove cannot delete body or head.
- Character categories come from `haven_assets` and are shared by Character Studio, the game creator model, and NPC generation rather than maintained as editor-only button lists.
- The Character Studio category control opens a direct category menu; previous/next remains only a convenience.

## Remaining composition convergence

W81R6 deliberately does not claim final Universal LPC layer-order parity. Character Studio still has a compatibility preview adapter while the exact sheet-definition / `zPos` resolver is the long-term composition authority. Any remaining clothing alignment defects after foundation correction should be resolved by moving Studio and runtime composition onto `UniversalLpcCharacterResolver`, not by accumulating more heuristic offsets.
