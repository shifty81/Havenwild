# Havenwild H21A14AB19-AB28 Player GUI Production Audit

## Scope
This batch deliberately preserves the current main menu. It targets the UI that appears after gameplay begins: HUD, equipment/inventory, crafting/station queues, map/minimap, pause/controls, status feedback and development telemetry separation.

## Major defects closed
- The runtime previously drew both the production bottom HUD and a second large prototype/debug HUD. Player mode now has one player HUD authority; development telemetry is a compact separate overlay.
- Hotbar slots previously used two-letter placeholders such as AX/PK/HO. They now use vector tool glyphs and separately show which actual main-hand tool is equipped.
- Gameplay tool selection no longer grants an imaginary unequipped tool. Non-hand actions require the corresponding equipped main-hand item.
- Inventory/crafting previously exposed long keyboard-instruction walls and raw internal identifiers. The production draw path uses bounded cards, compact key badges, elided labels, station readiness and queue progress.
- The Home Estate was still entering the continuous-surface minimap branch because it is an Exterior scene. The minimap now asks whether the active scene is a real streamed surface chunk. This avoids rebuilding a ContinuousSurfaceManifest every HUD frame while inside the bounded Estate.
- Map and pause panels now share the same runtime panel/slot vocabulary.

## Still intentionally separate
The title/main menu remains untouched. Character creation/world creation/loading are frontend flows and are not silently rewritten by this runtime GUI batch. Their existing UI documents remain the authority for a later focused frontend polish pass if visual testing shows they need it.

## Runtime acceptance
1. Enter the Dev Home Estate and confirm the bottom HUD is the only player HUD.
2. Confirm the Estate minimap displays local terrain and does not produce continuous-surface work each frame.
3. Open Inventory/Crafting and inspect every equipment slot, all 30 backpack slots, station controls, queue progress and recipe cards for overlap at the target desktop resolution.
4. Equip a crafted tool in Main Hand; its HUD glyph should show equipped state and its action should match the item.
5. Select a tool-belt entry without equipping that item; primary action must instruct the player to equip it rather than performing the tool action.
6. Open map, pause, controls and controller pages and verify consistent chrome and bounded labels.
