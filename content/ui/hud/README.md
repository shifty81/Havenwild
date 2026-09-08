# Havenwild Runtime HUD

The gameplay HUD is now a modular anchored composition rather than a full-width bottom bar.

Runtime-owned surfaces:

- top-left player card: code-generated wood/brass frame, live portrait, Health, Stamina, Hunger, Thirst, and expandable secondary needs;
- bottom-center hotbar: code-generated frame and slots; slots are player-authored inventory shortcuts and are never mapped to fixed tools;
- top-right minimap: project-owned `minimap_frame.png` overlay around the live circular minimap;
- minimap clock: live code-generated rotating day/night dial plus authoritative `HH:MM` game time inside the frame's lower-left clock housing;
- chat/dialogue/inventory/crafting/generic panels: consume the same scalable code-generated border grammar as they are normalized.

`vitals_frame.png` and `hotbar_frame.png` remain packaged only as legacy compatibility assets during migration; the active gameplay HUD does not use them as its visual authority.

## Hotbar authority

The hotbar is a shortcut view over owned items. Inventory drag/drop assigns any slot chosen by the player. The shortcut does not move or duplicate the underlying item. Right-click while Inventory is open clears a shortcut. The future radial menu must render these same persisted bindings rather than maintain a second assignment system.

## Minimap/clock authority

The minimap content remains live and circular. The frame is only an overlay. Time-of-day art and text are generated at runtime so they can animate continuously. Seasonal tint/ornament changes should bind to the future authoritative season runtime rather than being baked into static clock artwork.
