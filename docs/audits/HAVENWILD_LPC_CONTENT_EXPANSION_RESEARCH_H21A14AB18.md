# Havenwild LPC Content Expansion Research — H21A14AB9–AB18

## Decision
Havenwild should continue using the pinned Universal LPC repository as the character/equipment animation authority and ElizaWy/LPC plus governed OpenGameArt LPC sources as the principal compatible world-art/reference ecosystem. Third-party source archives remain outside normal patch/rollup payloads; the project registry records source URL, author/license, roles, and promotion state, and the local source-intake pipeline acquires them.

## Newly governed lanes
- **Hand Tools** — fully animated axe, pickaxe, hammer, shovel, hoe, watering can, fishing rod; used as the reference/conformance source for Havenwild work-tool animation.
- **Tavern** — inn/bar/kitchen/brewery furniture, props, lighting, food-service art and compatible lute/flute/drum animation.
- **Farming + Magic + UI** — additional crops/farming props, market/smithing props, magic effects, and wood/scroll UI reference motifs.
- **Extended Magic** — fire/water/ice/wind/lightning/shield effect reference lane.
- **Monsters** — creature attack animation reference lane.
- **Blacksmith / Woodshop / Tailor / Sawmill** — workshop/station visuals and animation references.
- **LPC Revised Workshop Tilesets** — reference-only reconciliation lane because it combines several upstream license/provenance sources; original governed providers remain promotion authority.

## Important ULPC audit finding fixed in this batch
The old repository indexer classified tools with substring matching. This made `pickaxe` match `axe`, `horseshoe` match `hoe`, and `waraxe` match the work axe. Shovel and whip were also absent from tool classification. The indexer now classifies exact source path families, and checked-in catalogs were regenerated to the corrected contract.

## Gameplay closure in this batch
- Crafted work tools now output the same `item.ulpc.*` identities consumed by equipment/action runtime.
- Axe and Mining Pick perform actual multi-hit resource interactions and grant inventory resources at the declared LPC animation contact point.
- Tree completion leaves a stump; stump/log/boulder/ore nodes use appropriate work-tool target rules.
- Loose mushroom/herb forage now produces inventory items; berry bushes become gathered-state objects instead of coin placeholders.
- Scythe clears tall grass into real fiber and no longer destroys generic crop state through the fallback path.

## Deliberately not falsely marked complete
- tool durability/quality/stat scaling;
- resource yield scaling from skills/professions;
- projectile simulation and ranged damage;
- spell gameplay effects;
- full combat hitbox/damage/AI integration;
- production sound/impact effect binding;
- automated promotion of share-alike art into the Havenwild-owned production lane.

Those remain explicit later gameplay/content passes. The source research is integrated now without allowing source artwork to become gameplay authority.

## Terrain transition extension

The governed intake now also includes **LPC terrain extension** as a first-class transition source. Its two-sided and three-sided contact tiles are especially relevant to Havenwild's exact-tuple terrain resolver because they cover edge-touching and multi-material junction shapes that the original rectangular LPC terrain pattern did not cover. This source is additive evidence/art, not permission to replace Havenwild semantic terrain or to silently substitute unrelated transition families.
