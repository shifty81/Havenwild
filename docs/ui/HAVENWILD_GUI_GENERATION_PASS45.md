# Havenwild GUI Generation Pass 45

The runtime currently has a basic debug/HUD layer but no real player-facing game GUI yet. This pass adds the GUI generation contract so inventory, storage, content browser, tool rail, dialogue, and validation widgets become metadata-backed assets rather than one-off drawn rectangles.

## Required GUI families

- HUD hotbar
- Inventory panel
- Storage/chest panel
- Asset/content browser panel
- Content browser tile card
- Tool rail button
- Tab button
- Scrollbar
- Tooltip
- Dialogue box
- Validation badge

## Required icon families

- food
- drink
- seed
- crop
- fish
- ore
- ingot
- tool
- furniture
- terrain
- zone
- transition
- NPC
- staff
- quest

## Editor/runtime rule

The standalone editor and the in-game dev overlay should consume the same catalogs, commands, and widget metadata. They can have different viewport hosts, but they should not become two separate tool systems.
