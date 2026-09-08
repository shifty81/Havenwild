# Havenwild Player Weapon / Tool / Crafting / UI Audit — H21A14AB8

This audit is based on the green H21A14AB7R1 source tree. The main menu is intentionally out of scope and should retain its current visual direction.

## KEEP — foundations that are already useful

### Universal equipment-to-animation binding

`universal_lpc_gameplay_equipment.rs` already maps equipment metadata to explicit gameplay actions:

- chop
- build
- till
- mine
- fish
- dig
- water
- slash
- thrust
- shoot
- spellcast
- block
- equip

Those actions resolve to real Universal LPC animation families and action durations. `gameplay_tool_runtime.rs` also waits for the declared animation contact point before committing the gameplay effect. This is the correct timing foundation and should remain authoritative.

### Existing crafting data/runtime foundation

`content/crafting/havenwild_crafting_catalog_v0_1.json` already defines hand crafting, workbench, campfire, primitive forge, and tailor bench stations with data-driven recipes. Player inventory runtime already contains station placement, fuel, input/output storage, processing queues, batch enqueue, pause/cancel/reorder, offline processing, and persistence foundations.

### Equipment persistence

Inventory/equipment persistence and Universal LPC equipment IDs are already connected. This should be extended rather than replaced.

## REWRITE / COMPLETE — current gameplay gaps

### Tools do not yet own type-correct resource interactions

The animation side is further along than the interaction side. Axe, pickaxe, and hammer currently fall through to generic `interact_with_tile_at()`. Many important resource objects in `runtime_interactions.rs` still return placeholder messages:

- Tree — chop placeholder
- Boulder — quarry placeholder
- OreNode — mining placeholder
- Bush / Mushroom / Herb — forage placeholders
- Stump / Log — harvest placeholders
- Well and several other world objects — placeholder interactions

The required target is one authoritative interaction/harvest system where the equipped item determines legal target classes, impact timing, stamina cost, tool wear/progression, damage/progress, sound, particles, target reaction animation, drops, XP/skill gain, and final state transition.

### Weapons are animation-capable but not combat-complete

The Universal LPC layer already exposes slash, thrust, shoot, spellcast and block animation categories, but runtime combat is not yet a full target/damage system. Scythe and Whip currently call a generic interaction/attack fallback; shoot/spellcast primarily report status text. Havenwild still needs weapon definitions, hit shapes/ranges, attack phases, damage/stat scaling, target filtering, projectiles where applicable, block/defense behavior, hit reactions, sounds/FX, drops and skill progression.

### Tool Belt / Hotbar authority is not yet the desired design

`GameplayTool::ALL` is currently a hardcoded ten-tool hotbar. The target project design is different:

- basic tools live in a persistent Tool Belt and do not consume ordinary inventory slots;
- the hotbar is a configurable quick-access bar;
- hotbar slots can point to Tool Belt tools, inventory items, weapons and consumables;
- slots render the real item/tool icon and state, not text abbreviations as primary presentation.

The hardcoded enum can remain as compatibility/default-tool IDs, but it should stop being the player-facing hotbar authority.

### Farming interaction/presentation still needs closure

Hoe/watering/scythe/shovel currently mutate semantic tiles directly. That is a valid low-level operation but is not yet the complete farming interaction contract. Tilled/watered soil needs connected edge/corner presentation, coherent drag/area authoring behavior, impact feedback and crop-state integration. The isolated brown squares visible in current testing are part of this gap.

## Player-facing UI audit

### Current inventory/crafting UI is a functional debug/prototype surface

`player_inventory_ui/draw.rs` draws one hardcoded Macroquad panel named `Inventory & Crafting`. It contains text-heavy equipment slots, inventory cells, a 2x2 crafting grid, station status, recipe rows, raw item IDs in requirements, and numerous keyboard hints embedded directly into the panel.

This is useful for proving systems but is not production UI.

### Existing authored UI document is not the runtime authority

`content/ui/documents/crafting.ui.json` exists, but the live player inventory/crafting screen is still hardcoded by `player_inventory_ui/draw.rs`. The runtime needs a shared player-facing UI skin/widget layer rather than continuing to grow one-off drawing code.

### Required post-main-menu UI direction

Preserve the current main menu. Normalize everything after it around one production player UI language:

- inventory with real item icons, rarity/state overlays, stack counts and tooltips;
- equipment paper doll / readable equipment slots;
- dedicated Tool Belt presentation;
- configurable hotbar tied to actual inventory/Tool Belt references;
- crafting recipe browser with categories/search/filtering and real ingredient icons;
- station UI that visually separates input, fuel, queue/progress and output;
- interaction prompt showing target, required/equipped tool and action;
- combat feedback (health/stamina, target feedback, status effects where applicable);
- consistent buttons, tabs, panels, typography, spacing and focus/navigation behavior;
- controller/mouse/keyboard prompts sourced from the control binding system rather than hardcoded key letters;
- no changes to the existing main-menu visual direction unless a regression requires it.

## Recommended implementation sequence after AB8

1. **Tool Belt + configurable Hotbar authority** — inventory references instead of hardcoded tool selection.
2. **Resource Interaction/Harvest authority** — Tree/Boulder/Ore/Log/Stump/forage targets with synchronized animation/contact/sound/FX/drop state.
3. **Weapon/Combat authority** — melee/thrust/ranged/block target and damage pipeline using the existing Universal LPC action bindings.
4. **Crafting catalog normalization** — recipe/item IDs, progression, stations, tool/weapon recipes and equipment upgrades.
5. **Player UI shell production pass** — reusable post-main-menu panel/button/slot/tooltip skin and layout.
6. **Inventory + Equipment + Tool Belt + Hotbar UI**.
7. **Crafting/Station UI**.
8. **Interaction/Combat HUD polish**.
9. **Farming soil/crop presentation closure** including connected tilled/watered soil.

The key rule is that visuals never fake capability: every displayed tool, weapon, recipe, station control or interaction prompt must resolve to the same authoritative gameplay definition used by runtime execution.
