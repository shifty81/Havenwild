# Workspace Architecture

## Rust Crates

- `haven_core`: pure shared gameplay data, tiles, maps, objects, zones, scenes, save/export bridge types.
- `haven_world`: region graph, scene rectangles, worldgen load/export boundaries, and world-scale contracts.
- `haven_assets`: generated asset registry, autotiling, animation contract, and asset lookup rules.
- `haven_editor`: shared editor spine, validation, project file, command bus, and inspection APIs.
- `haven_game`: forward runtime package name that currently includes the playable Macroquad runtime.
- `haven_save`, `haven_sim`, `haven_net`, `haven_render`, `haven_tools`: staged domain crates for the long-term split.
- `haven_core`, `haven_editor`, `haven_game`: compatibility/prototype entrypoints retained during migration.
- `haven_editor`: standalone native Rust editor shell.

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
- a standalone Rust tool for full world, region graph, scene, validation, asset, animation, and scripting authoring
- a browser tool only for lightweight structured content and preview workflows

Authoring is deliberately data-first: canonical commands, terrain policy, inspection/validation, capabilities, and the default construction palette live in `haven_authoring`; the native developer editor and in-game Player World Builder are separate frontends over those shared contracts. Map/object definitions live in `haven_core`, world-scale contracts live in `haven_world`, and asset/autotile/animation contracts live in `haven_assets`.

## Implemented Editor Foundations

- Cell inspector from `haven_editor::inspect_cell`.
- Simple line-based map save/load format via `TavernMap::serialize_lines` and `TavernMap::deserialize_lines`.
- `F5` saves to `workspace/saves/starter.tmap`.
- `F9` loads from `workspace/saves/starter.tmap`.
- Asset metadata model starts with `AssetRecord`.
- Generated worldgen asset registry reads `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`.
- Game rendering now uses deterministic tile variation/detail as a bridge toward sprite-backed tile variants.
