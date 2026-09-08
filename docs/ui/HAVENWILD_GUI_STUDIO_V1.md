# Havenwild GUI Studio V1

GUI Studio is a first-class workspace inside the single Havenwild native editor executable.

## Ownership

- `content/ui/gui/havenwild_gui_component_catalog_v1.json` owns the reusable component catalog.
- Reference PNGs are concept/source material until each element receives reviewed slice bounds and 9-slice margins.
- Runtime owns bar fills, values, text, character portraits, inventory items, minimap contents, clock state, focus, hover, pressed, disabled, and selected states.
- UI artwork must not contain baked values or gameplay state.

## Initial documents

- Gameplay HUD
- Character Inventory
- New World Creation
- Dialogue
- Generic Panel

## Next production wiring

1. Add reviewed sprite slicing metadata for the rustic UI sheet.
2. Add `GuiDocumentV1` persistence and undoable widget commands.
3. Connect Inventory to authoritative character/equipment data.
4. Connect New World Creation to `WorldManifestV2` and generation settings.
5. Add live runtime preview and resolution/safe-area presets.
