# Pass 137 — Character Profile, Wardrobe, and Progression Gate

## Result

Pass 137 advances the appearance-first character creator into a runtime-safe profile contract.

### Added

- Canonical `CharacterProfileSelection` save-facing structure.
- Catalog-driven default appearance and starter-clothing selection.
- Explicit color-channel policy for body/head, hair-family, eyes, and starter clothing.
- Initial-creator slot allowlist: `top`, `bottom`, and `feet` only.
- Progression-only gates for armor, weapons, shields, and advanced outfits.
- Cross-validation between the creation catalog, profile policy, and selected profile.
- Neutral side-idle requirements remain separate from walk frames.

## Architectural rule

The character creator stores semantic option IDs and color values. It does not store atlas coordinates. Asset-role resolution, animation compositing, equipment rendering, and later asset replacement remain downstream responsibilities.

## Next pass

Pass 138 should connect these contracts to the client character-creation state and preview compositor, then serialize the selected persistent character profile separately from world/save-slot data.
