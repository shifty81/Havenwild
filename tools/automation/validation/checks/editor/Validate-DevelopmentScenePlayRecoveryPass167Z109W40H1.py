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


def main() -> int:
    descriptor = json.loads(text("WORKSPACE/development/active_world.json"))
    editor_mod = text("apps/haven_editor_native/src/app/mod.rs")
    editor_menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
    development_session = text("apps/haven_editor_native/src/app/development_session.rs")
    client_entry = text("crates/haven_game/src/client_entry.rs")
    game_main = text("crates/haven_game/src/main.rs")
    terrain_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")

    req(descriptor.get("default_scene") == "farmstead",
        "development descriptor must anchor the native editor to canonical Farmstead")
    req(descriptor.get("spawn") == {"x": 48, "y": 40},
        "development descriptor Farmstead spawn must match the canonical authored scene")

    req("app.ensure_scene_visible();" in editor_mod,
        "startup-selected development scene must be scrolled into the scene list")
    req("app.scene_cursor_x = scene.spawn_x;" in editor_mod
        and "app.scene_cursor_y = scene.spawn_y;" in editor_mod,
        "native editor startup cursor must use the selected SceneMap canonical spawn")
    req('ProjectSceneId::new("farmstead")' in editor_mod,
        "native editor must retain canonical Farmstead fallback if descriptor scene becomes stale")

    req("let mut published_world = self.model.world.clone();" in editor_menu,
        "Play must publish an editor-owned world snapshot")
    req("published_world" in editor_menu and ".set_active_scene(" in editor_menu,
        "Play must make the editor-selected scene active in the published world")
    req("&published_world" in editor_menu and "save_world_to_path" in editor_menu,
        "Play must save the scene-authoritative published snapshot")
    req("Some(selected_scene_spawn)" in editor_menu,
        "normal Play must launch at the selected scene canonical spawn")
    req("Some([self.scene_cursor_x, self.scene_cursor_y])" in editor_menu,
        "Play From Here must preserve explicit editor cursor spawn")
    req("Development Play launch:" in editor_menu,
        "native editor must log exact development scene/spawn launch authority")

    req("let preferred_x = scene.spawn_x" in development_session
        and "let preferred_y = scene.spawn_y" in development_session,
        "development acceptance fixture must follow SceneMap spawn authority")
    req("attach_development_client_stdio" in development_session
        and "haven_development_client_stdio.log" in development_session
        and "command.stderr(Stdio::from(stderr_file))" in development_session,
        "native-editor development launches must preserve child stdout/stderr diagnostics")
    req("descriptor.spawn.x + DEVELOPMENT_ACCEPTANCE_CRATE_OFFSET" not in development_session,
        "descriptor spawn must not remain a second acceptance-fixture authority")

    req("falling back to canonical scene spawn" in client_entry,
        "invalid development spawn must recover rather than immediately close the client")
    req("Development launch failed before runtime ready" in client_entry,
        "pre-runtime development failure must be written to the game log")
    req("return Err(format!(\"development spawn" not in client_entry,
        "out-of-bounds development spawn must not terminate the development client")

    req("install_game_panic_log_hook();" in game_main
        and 'haven_game_crash.log' in game_main
        and "Backtrace::force_capture()" in game_main,
        "game development crashes must leave a durable panic/backtrace log")

    # Preserve the W39/W40 visual-authority recovery while fixing scene Play.
    req("parse_generated_chunk_scene_id(active_scene_id).is_some()" in terrain_pass
        and "parse_pcg_surface_scene_id(active_scene_id).is_some()" in terrain_pass,
        "W39 authored-exterior renderer dispatch guard was lost")

    print("Pass167Z109W40H1 development scene/play recovery validated")
    print("- Farmstead is visible and authoritative on editor startup")
    print("- editor-selected scene + canonical spawn are authoritative for Play")
    print("- invalid dev spawns recover and game panics leave durable logs")
    print("- W39 authored-exterior dispatch remains guarded")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W40H1 validation FAILED: {exc}")
        raise SystemExit(1)
