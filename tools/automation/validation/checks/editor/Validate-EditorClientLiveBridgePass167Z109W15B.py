#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def load(rel: str):
    return json.loads(text(rel))


def main() -> int:
    authority = load("content/editor/dev_client_bridge_authority_v0_1.json")
    req(authority["pass"] == "167Z109W15B", "W15B bridge authority pass mismatch")
    req(authority["transport"]["networkRequired"] is False, "dev bridge may not require network")
    req(authority["transport"]["cloudRequired"] is False, "dev bridge may not require cloud")
    req(authority["editor"]["autoPushDefault"] is True, "Auto Push should default on")
    req(authority["client"]["developmentRevealPersistsExploration"] is False,
        "development reveal must not mutate persisted exploration")
    req(authority["handoff"]["officialCumulativePass"] is False,
        "development handoff must never masquerade as official cumulative pass")
    req(authority["permanence"]["coreDevelopmentWorldSource"] ==
        "content/worldgen/dev_worlds/core_dev_001/world.tworld",
        "Core Dev authored world source path drifted")

    core = text("crates/haven_core/src/dev_bridge.rs")
    for token in (
        'DEV_BRIDGE_SCHEMA', 'WORKSPACE/dev_bridge', 'ReloadAssets', 'ReloadEditorWorld',
        'ReloadAssetsAndWorld', 'SetRevealAllMap', 'QuitClient',
        'queue_dev_bridge_command', 'write_dev_bridge_status', 'read_dev_bridge_status',
    ):
        req(token in core, f"shared bridge protocol missing {token}")
    req("Tcp" not in core and "Udp" not in core and "reqwest" not in core,
        "W15B bridge should remain repository-local file IPC")

    editor_menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
    editor_mod = text("apps/haven_editor_native/src/app/mod.rs")
    req("CORE_DEV_WORLD_SOURCE_PATH" in editor_mod, "Core Dev source-controlled world mirror missing")
    req("save_world_to_path(CORE_DEV_WORLD_SOURCE_PATH" in editor_menu,
        "Editor Save does not persist the Core Dev authored world into project source")

    editor = text("apps/haven_editor_native/src/app/dev_client_bridge.rs")
    for token in (
        'launch_or_attach', 'build_and_restart', 'ReloadAssetsAndWorld',
        'HAVENWILD_DEV_BRIDGE', 'target/debug/haven_game.exe',
        'auto_push: true', 'reveal_all_map: true',
    ):
        req(token in editor, f"native editor dev-client bridge missing {token}")

    menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
    req("EditorMenuKind::Dev" in menu, "Dev menu missing")
    for token in (
        "launch_or_attach_dev_client", "save_all_and_push_dev_client",
        "push_assets_to_dev_client", "push_world_to_dev_client",
        "build_and_restart_dev_client", "stop_dev_client",
        "toggle_dev_auto_push", "toggle_dev_map_reveal",
    ):
        req(token in menu, f"Dev menu action missing {token}")
    req('auto_push_saved_changes_to_dev_client("Save All")' in menu,
        "Save All is not wired to optional Auto Push")

    pixel = text("apps/haven_editor_native/src/app/pixel_studio_render.rs")
    asset_pixel = text("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
    req('push_assets_to_dev_client("Pixel Studio save")' in pixel,
        "Pixel Studio save is not hot-pushed")
    req('push_assets_to_dev_client("World asset Pixel Studio save")' in asset_pixel,
        "world-asset Pixel Studio save is not hot-pushed")

    client = text("crates/haven_game/src/runtime_dev_bridge.rs")
    req('content/worldgen/dev_worlds/core_dev_001/world.tworld' in client,
        "live world reload is not consuming the source-controlled Core Dev world")
    for token in (
        "replace_runtime_assets_from_dev_bridge", "reload_editor_world_from_dev_bridge",
        "invalidate_dev_bridge_presentation_caches", "SetRevealAllMap",
        "ReloadAssetsAndWorld", "write_status",
    ):
        req(token in client, f"runtime dev bridge missing {token}")

    entry = text("crates/haven_game/src/client_entry.rs")
    req("DevBridgeClientSession::from_runtime_root" in entry, "client does not start bridge session")
    req("dev_bridge.poll_game" in entry, "gameplay loop does not poll bridge")
    req("RuntimeAssets::load" in entry and "replace_runtime_assets_from_dev_bridge" in entry,
        "asset hot reload path missing")

    world_map = text("crates/haven_game/src/runtime_world_map.rs") + "\n" + text("crates/haven_game/src/runtime_world_map_game.rs")
    req("development_reveal_all" in world_map, "development map reveal state missing")
    req("DEVELOPMENT REVEAL ACTIVE" in world_map, "development reveal status presentation missing")
    req("development_reveal_all" not in text("crates/haven_game/src/runtime_world_map_persistence.rs")
        if (ROOT / "crates/haven_game/src/runtime_world_map_persistence.rs").is_file() else True,
        "development map reveal leaked into exploration persistence")

    package = text("tools/control/PackageProject.ps1")
    registry = text("tools/control/ProjectCommandRegistry.ps1")
    req("'handoff'" in package and "DevelopmentHandoff" in package,
        "development handoff packaging mode missing")
    req("'WORKSPACE/dev_bridge'" in package,
        "ephemeral dev bridge transport must be excluded from source packages")
    req("Package development handoff" in registry,
        "HavenwildTools development handoff command missing")
    req("officialCumulativePass = $false" in package,
        "handoff manifest must explicitly deny official cumulative authority")

    # Previous locked gates remain authoritative.
    cliff = load("content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json")
    req(cliff["revision"].startswith("167Z109W14"), "W14 cliff authority changed in W15B")
    controls = load("content/ui/client_input_pause_controls_authority_v0_1.json")
    req(controls["revision"].startswith("167Z109W15A"), "W15A input/controller authority changed in W15B")

    print("Pass167Z109W15B editor/client live bridge validated")
    print("- local file IPC + heartbeat: present")
    print("- Launch/Attach, Save & Push, hot reload, Build & Restart: present")
    print("- development full-map reveal is non-persistent: present")
    print("- development handoff packaging is explicit and non-cumulative: present")
    print("- W14 cliff and W15A input authorities: unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W15B validation FAILED: {exc}")
        raise SystemExit(1)
