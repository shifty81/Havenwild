#!/usr/bin/env python3
"""Validate the haven_game authored terrain-contact import surface."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    main_rs = read("crates/haven_game/src/main.rs")
    startup = read("crates/haven_game/src/runtime_startup.rs")
    world_paint = read("crates/haven_game/src/world_paint_editor_panel.rs")
    runtime_editor = read("crates/haven_game/src/runtime_editor_shell.rs")
    contacts = read("crates/haven_assets/src/authored_terrain_contacts.rs")
    assets_lib = read("crates/haven_assets/src/lib.rs")

    import_line = (
        "use haven_assets::authored_terrain_contacts::"
        "normalize_lpc_authored_material_contacts_region;"
    )
    require(
        main_rs.count(import_line) == 1,
        "haven_game must import the authored contact normalizer exactly once",
        errors,
    )
    require(
        "normalize_lpc_authored_material_contacts_region(" in startup,
        "startup migration call site is missing",
        errors,
    )
    require(
        "normalize_lpc_authored_material_contacts_region(" in world_paint,
        "world-paint contact repair call site is missing",
        errors,
    )
    require(
        "pub fn normalize_lpc_authored_material_contacts_region" in contacts,
        "authored terrain-contact normalizer is not public",
        errors,
    )
    require(
        "pub mod authored_terrain_contacts;" in assets_lib,
        "haven_assets does not export authored_terrain_contacts",
        errors,
    )
    require(
        "normalize_shore_water_lifecycle_region" not in runtime_editor,
        "ordinary F3 runtime editor directly calls broad shoreline lifecycle",
        errors,
    )

    if errors:
        print("Pass167Z71 terrain contact import surface validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Pass167Z71 terrain contact import surface validation passed")
    print("- startup and World Paint share one restored parent-module import")
    print("- Exact terrain editing remains isolated from broad shoreline lifecycle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
