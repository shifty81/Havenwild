# Travellers Rest Research Snapshot

Date: 2026-05-24

## Public Facts

- Steam lists Travellers Rest as developed by Isolated Games and published by Isolated Games / IndieArk, released July 28, 2020.
- Steam describes the game around crafting, farming, building, cooking, tavern keeping, dishes, drinks, customers, and world/character discovery.
- The official wiki describes the tavern as the central hub, with farm plots, a highway/customer arrival path, postbox, delivery chest, bin, notice board, well, interior floors, cellar, guest rooms, and Construction Mode.
- Public wiki mechanics categories include tavern management, construction mode, brewing, farming, orders, staff, guest rooms, trends, VIP, animals, fishing, foraging, beekeeping, and irrigation.
- Existing local notes indicate your mod-kit research found the installed game is Unity 2022.3.62 through BepInEx logs. The standalone remake will use Rust instead.

## Design Translation

For our standalone Rust game, the relevant system pillars are:

- Tavern service loop: open/close, customers, patience, seating, orders, reputation, money.
- Construction loop: floors, walls, rooms, zones, placeables, deletion/recovery, validation.
- Production loop: cooking, brewing, aging, kegs, cellars, shelves, quality, trends.
- Farming loop: tilling, greenhouse zones, crops, seasons, water/irrigation.
- Staff loop: bartender, waiter, bouncer, housekeeper-like roles with original names.
- Editor loop: live map editing, asset catalog, content packs, script hooks, validation.

## Legal Boundary

We can model broad mechanics and workflows. We should not copy:

- Original Travellers Rest sprites, icons, UI, maps, audio, writing, item names, or proprietary data.
- Exact layout dimensions, exact recipes/economy values, or distinctive content expression.
- Decompiled code or extracted assets into the standalone game.

Use owned game screenshots only as private inspiration and QA reference, not as source assets.

## Sources

- Steam page: https://store.steampowered.com/app/1139980/Travellers_Rest/
- Official wiki home: https://travellersrest.wiki.gg/
- Tavern page: https://travellersrest.wiki.gg/wiki/Tavern
- Game mechanics category: https://travellersrest.wiki.gg/wiki/Category:Game_Mechanics
- Farming page: https://travellers-rest.fandom.com/wiki/Farming
