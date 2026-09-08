# Havenwild W60C — Canvas UX & Asset Browser Normalization

W60C normalizes the native editor around one canvas-authoring language instead of adding another panel-specific toolbar.

## Layer pane

The layer stack is an opaque docked pane beside the canvas. A row intentionally shows only three authoring signals: visibility, the layer title, and lock state. Selecting a layer changes context only; it never arms Paint, Place, Collision, or another modifying operation.

## Central tool rail

The full-height left rail is the one canonical canvas tool selector. Tools are organized into Pointer, Brushes, Shapes, Content, and Gameplay groups. A group opens a popup containing its applicable tools and their shortcuts. Tool availability is resolved from the current workspace and active layer. Unsupported tools stay spatially stable but render disabled and cannot be activated.

Workspace top bars are reserved for view/document/transport/mode commands. Pixel Studio's duplicate Pencil/Eraser/Fill/Pick/etc. selector was removed, as were duplicate Select/Pan selectors in world/scene-bank chrome.

Icons are project-owned vectors using familiar editor metaphors (pointer/marquee/hand, pencil/eraser/bucket/eyedropper, shape, move, link, collision, socket, event) rather than text initials.

## Asset browsers

A shared thumbnail-card layout is used by Pixel Studio, Animation Studio, the Scene asset palette, and the Content Library. Visible Pixel/Animation images are lazily loaded with nearest-neighbor filtering and a bounded GPU cache. Selecting an asset changes the selected resource only; it does not implicitly enter Paint or Place.

## Color and palette

Pixel Studio keeps the compact palette at the bottom for rapid foreground/background selection. `Color Wheel` opens the full color controls as a floating panel so advanced color work does not permanently consume canvas space.

## Help and key bindings

F1 opens the in-application Help Center. It includes a keyboard-shortcut page sourced from the same ToolRegistry that drives the tool rail, plus Canvas & Layers, Asset Browsers, Pixel/Junction Authoring, and Color & Palette topics.

This is the first native-editor help/wiki surface. It should grow by data/topic rather than adding disconnected help popups to individual workspaces.

## External UX references

W60C uses established interaction patterns without copying another application's chrome: Aseprite's single tool bar plus separate color/palette surface, Krita's dockers/grouped brush presets/pop-up palette, LDtk's layer sidebar/context palette/shortcut cheat sheet, and thumbnail-oriented project browsers used by game editors such as Godot.

## Acceptance

1. Layer pane never visually overlaps editable canvas content and contains only visibility/title/lock rows.
2. Tool rail spans the available canvas height and grouped buttons use recognizable icons.
3. Clicking a tool group shows its tool popup; disabled tools are grey and cannot activate.
4. Selecting an asset or layer never silently starts painting/placing.
5. Pixel Studio does not duplicate drawing tools across both left and top chrome.
6. Pixel and Animation source browsers show thumbnail cards rather than text-only rows.
7. Scene asset palette and Content Library use the same card language.
8. Color Wheel opens as a floating panel and can be dismissed without changing the active tool.
9. F1 opens the Help Center and its shortcut page reflects the active canvas/tool registry.
10. Segoe UI authority from W60B remains unchanged.
