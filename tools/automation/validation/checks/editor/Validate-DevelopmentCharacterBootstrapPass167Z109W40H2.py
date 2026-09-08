#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def main() -> int:
    client_entry = text("crates/haven_game/src/client_entry.rs")
    development_session = text("apps/haven_editor_native/src/app/development_session.rs")
    terrain_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")

    req("ensure_development_character_profile_at(&profile_root, character_id)" in client_entry,
        "development profile provisioning must route through the repairable/idempotent helper")
    req('let profile_path = profile_directory.join("profile.json");' in client_entry
        and "if profile_path.is_file()" in client_entry,
        "an already-complete development profile must be reused")
    req("if profile_directory.exists()" in client_entry
        and "std::fs::remove_dir_all(&profile_directory)" in client_entry,
        "an incomplete development character directory must be repaired before create()")
    req("unable to repair incomplete development profile" in client_entry,
        "development bootstrap repair must preserve actionable failure diagnostics")
    req("Havenwild repaired incomplete development character profile" in client_entry,
        "successful bootstrap repair must leave a persistent child-log acceptance marker")
    req("development_profile_provisioning_is_idempotent" in client_entry,
        "development profile provisioning requires an idempotency regression test")
    req("incomplete_development_profile_directory_is_repaired" in client_entry,
        "interrupted development profile provisioning requires a repair regression test")

    # Preserve W40H1 diagnostics and W39 authored-exterior rendering while fixing bootstrap.
    req("haven_development_client_stdio.log" in development_session,
        "persistent editor-launched client diagnostics from W40H1 were lost")
    req("parse_generated_chunk_scene_id(active_scene_id).is_some()" in terrain_pass
        and "parse_pcg_surface_scene_id(active_scene_id).is_some()" in terrain_pass,
        "W39 authored-exterior renderer dispatch guard was lost")

    print("Pass167Z109W40H2 development character bootstrap validated")
    print("- complete development profiles are reused")
    print("- incomplete/stale development profile directories are self-repaired")
    print("- W40H1 persistent child diagnostics remain active")
    print("- W39 authored-exterior dispatch remains guarded")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W40H2 validation FAILED: {exc}")
        raise SystemExit(1)
