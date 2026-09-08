# Workspace Architecture

## Rust Crates

- `haven_core`: pure shared data model and rules.
- `haven_game`: playable native game using macroquad.
- `haven_editor`: editor palette, validation, future scripting/content-pack tooling.

## Data Folders

- `assets/raw`: downloaded or hand-made source art/audio, with licenses.
- `assets/processed`: packed/generated runtime assets.
- `content/packs`: JSON/TOML content packs.
- `content/schemas`: schemas and validation rules.
- `workspace/imports`: external dumps, references, and unprocessed imports.
- `logs`: build/game/editor logs.

## Logging

- `tools/build/Build.ps1` writes menu and command logs to `logs/build-menu-*.log`.
- `haven_game` writes runtime events to `logs/haven_game.log`.
- Future editor/content scripts should write logs under `logs/` and avoid silent mutations.

## Editor Strategy

The editor should run both as:

- an in-game overlay for immediate map/construction iteration
- a standalone tool for content packs, asset metadata, validation, and scripting

The first editor implementation is deliberately data-first: construction tools come from `haven_editor::EditorPalette`, while map/object definitions live in `haven_core`.
