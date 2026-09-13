# Forge GUI Portable Stack Direction

ForgePY's GUI direction should become a portable module family rather than a one-off application skin.

## Required reusable layers

- Theme tokens: surfaces, borders, text, accent, danger/warn/pass, spacing, radius, typography.
- Widgets: buttons, toggles, segmented controls, tabs, toolbars, inspectors, trees, lists, grids, property rows, search fields.
- Panels: docked, floating, locked, collapsed, split, tabbed, canvas-hosted.
- Workspaces: project dashboard, asset mapping, pixel editor, animation editor, scene/room editor, node/logic editor.
- Activity surfaces: console, problems, build, git, patch intake, asset validation.

## Havenwild usage

Havenwild should consume this look/behavior immediately in project-local form. Once stable, Ember should own the generic implementation.
