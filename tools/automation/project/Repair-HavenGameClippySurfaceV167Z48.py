#!/usr/bin/env python3
"""Repair the Haven game Clippy surface exposed after Pass 167Z47.

The migration is intentionally idempotent and narrow:
- removes three truly unused Game scratch/cache fields and their constructors;
- removes the unused cycle-enum ordinal helper;
- moves the generated HeadwearKind compatibility impl before the test module;
- removes superseded title-art helpers that have no active callers;
- modernizes two Option fallbacks and two Default-based initializers;
- marks only staged crafting/station UI hooks as deliberately dormant.

It does not change runtime terrain, LPC mappings, character layer selection,
world-generation rules, save schemas, or gameplay behavior.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVISION = "167Z48-haven-game-clippy-surface-repair-v1"


def read(relative: str, *, required: bool = True) -> str | None:
    path = ROOT / relative
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"required source file missing: {relative}")
        return None
    return path.read_text(encoding="utf-8")


def write_if_changed(relative: str, original: str, updated: str, changes: list[str]) -> None:
    if updated == original:
        return
    path = ROOT / relative
    path.write_text(updated, encoding="utf-8", newline="\n")
    changes.append(relative)


def _matching_brace(text: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = 0
    index = open_index
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "/" and nxt == "*":
                block_comment += 1
                index += 2
                continue
            if char == "*" and nxt == "/":
                block_comment -= 1
                index += 2
                continue
            index += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char == "/" and nxt == "/":
            line_comment = True
            index += 2
            continue
        if char == "/" and nxt == "*":
            block_comment = 1
            index += 2
            continue
        if char == '"':
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError(f"unbalanced Rust block beginning at byte {open_index}")


def _line_start(text: str, index: int) -> int:
    return text.rfind("\n", 0, index) + 1


def _line_end(text: str, index: int) -> int:
    end = text.find("\n", index)
    return len(text) if end < 0 else end + 1


def remove_function(text: str, name: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"(?m)^(?P<indent>[ \t]*)(?:(?:pub(?:\([^\n)]*\))?\s+)?(?:async\s+)?fn\s+{re.escape(name)}\s*\()"
    )
    match = pattern.search(text)
    if not match:
        return text, False
    start = match.start()
    # Include immediately preceding attributes, but not unrelated comments/items.
    cursor = start
    while cursor > 0:
        previous_end = cursor - 1
        previous_start = text.rfind("\n", 0, previous_end) + 1
        line = text[previous_start:cursor].strip()
        if line.startswith("#["):
            cursor = previous_start
            continue
        break
    brace = text.find("{", match.end())
    if brace < 0:
        raise ValueError(f"function {name} has no body")
    close = _matching_brace(text, brace)
    end = _line_end(text, close)
    updated = text[:cursor] + text[end:]
    return updated, True


def remove_const(text: str, name: str) -> tuple[str, bool]:
    pattern = re.compile(rf"(?m)^[ \t]*(?:pub(?:\([^\n)]*\))?\s+)?const\s+{re.escape(name)}\b[^;]*;\s*\n?")
    updated, count = pattern.subn("", text, count=1)
    return updated, bool(count)


def add_allow_before_item(text: str, item_pattern: str) -> tuple[str, bool]:
    pattern = re.compile(item_pattern)
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    changed = False
    for line in lines:
        if pattern.search(line):
            previous = output[-1].strip() if output else ""
            if previous != "#[allow(dead_code)]":
                indent_match = re.match(r"[ \t]*", line)
                indent = indent_match.group(0) if indent_match else ""
                output.append(f"{indent}#[allow(dead_code)]\n")
                changed = True
        output.append(line)
    return "".join(output), changed


def repair_game_scratch_fields(changes: list[str]) -> None:
    main_relative = "crates/haven_game/src/main.rs"
    original = read(main_relative)
    assert original is not None
    updated = original
    for field in (
        "actor_render_scratch",
        "runtime_diagnostics_cache",
        "runtime_diagnostics_next_refresh_at",
    ):
        updated = re.sub(rf"(?m)^[ \t]*{field}\s*:[^\n]+\n", "", updated)
    write_if_changed(main_relative, original, updated, changes)

    bootstrap_relative = "crates/haven_game/src/game_bootstrap.rs"
    original = read(bootstrap_relative)
    assert original is not None
    updated = original
    for field in (
        "actor_render_scratch",
        "runtime_diagnostics_cache",
        "runtime_diagnostics_next_refresh_at",
    ):
        updated = re.sub(rf"(?m)^[ \t]*{field}\s*:[^\n]+\n", "", updated)
    write_if_changed(bootstrap_relative, original, updated, changes)


def repair_creator_surface(changes: list[str]) -> None:
    relative = "crates/haven_game/src/character_creator_model.rs"
    original = read(relative)
    assert original is not None
    updated = original

    # The ordinal helper is no longer used by the current creator UI.
    while True:
        candidate, removed = remove_function(updated, "ordinal")
        if not removed:
            break
        updated = candidate

    # Pass Z46 appended a compatibility impl after the test module on some baselines.
    test_match = re.search(r"(?m)^#\[cfg\(test\)\].*$", updated)
    if test_match:
        impl_match = re.search(r"(?m)^impl\s+HeadwearKind\s*\{", updated[test_match.start():])
        if impl_match:
            impl_start = test_match.start() + impl_match.start()
            brace = updated.find("{", impl_start)
            impl_end = _matching_brace(updated, brace)
            block_start = _line_start(updated, impl_start)
            # Preserve the generated explanatory comment with the impl when present.
            previous_start = updated.rfind("\n", 0, max(0, block_start - 1)) + 1
            previous_line = updated[previous_start:block_start]
            if "Pass 167Z46" in previous_line:
                block_start = previous_start
            block_end = _line_end(updated, impl_end)
            block = updated[block_start:block_end].strip("\n") + "\n\n"
            updated = updated[:block_start] + updated[block_end:]
            insert_at = re.search(r"(?m)^#\[cfg\(test\)\].*$", updated)
            if insert_at:
                updated = updated[:insert_at.start()] + block + updated[insert_at.start():]

    write_if_changed(relative, original, updated, changes)


def repair_superseded_title_art(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_character_frontend_draw.rs"
    original = read(relative)
    assert original is not None
    updated = original
    for name in (
        "title_art_rect",
        "draw_title_art",
        "title_source_rect",
        "title_banner_rect",
        "title_menu_layout",
        "draw_title_banner",
        "draw_title_menu_button_image",
    ):
        updated, _ = remove_function(updated, name)
    for name in ("TITLE_SOURCE_W", "TITLE_SOURCE_H"):
        updated, _ = remove_const(updated, name)
    write_if_changed(relative, original, updated, changes)


def repair_compositor_clippy(changes: list[str]) -> None:
    relative = "crates/haven_game/src/character_runtime_compositor.rs"
    original = read(relative)
    assert original is not None
    updated = original.replace(
        ".or_else(|| layer.idle_texture.as_ref())",
        ".or(layer.idle_texture.as_ref())",
    )
    write_if_changed(relative, original, updated, changes)


def repair_default_initializers(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_save_generation.rs"
    original = read(relative)
    assert original is not None
    updated = re.sub(
        r"let\s+mut\s+settings\s*=\s*WorldCreationSettings::default\(\);\s*\n"
        r"(?P<indent>[ \t]*)settings\.display_name\s*=\s*display_name\.into\(\);\s*\n"
        r"(?P=indent)settings\.seed\s*=\s*seed;",
        "let settings = WorldCreationSettings {\n"
        "        display_name: display_name.into(),\n"
        "        seed,\n"
        "        ..Default::default()\n"
        "    };",
        original,
        count=1,
    )
    write_if_changed(relative, original, updated, changes)

    relative = "crates/haven_game/src/world_creation_wizard.rs"
    original = read(relative)
    assert original is not None
    updated = re.sub(
        r"let\s+mut\s+settings\s*=\s*WorldCreationSettings::default\(\);\s*\n"
        r"(?P<indent>[ \t]*)settings\.seed\s*=\s*seed\.max\(1\);\s*\n"
        r"(?P=indent)settings\.display_name\s*=\s*display_name\.into\(\);",
        "let settings = WorldCreationSettings {\n"
        "            seed: seed.max(1),\n"
        "            display_name: display_name.into(),\n"
        "            ..Default::default()\n"
        "        };",
        original,
        count=1,
    )
    write_if_changed(relative, original, updated, changes)


def repair_staged_ui_lints(changes: list[str]) -> None:
    targets: dict[str, list[str]] = {
        "crates/haven_game/src/player_inventory_ui.rs": [
            r"^[ \t]*(?:pub\(crate\)\s+)?struct\s+CraftingStationDefinition\b",
            r"^[ \t]*pub\(crate\)\s+input_slots\s*:",
            r"^[ \t]*pub\(crate\)\s+output_slots\s*:",
            r"^[ \t]*pub\(crate\)\s+fuel_slots\s*:",
            r"^[ \t]*pub\(crate\)\s+recipe_category\s*:",
            r"^[ \t]*struct\s+StationNotification\b",
            r"^[ \t]*message\s*:",
            r"^[ \t]*created_at\s*:",
            r"^[ \t]*const\s+STATION_NOTIFICATION_SECONDS\b",
            r"^[ \t]*pub\(crate\)\s+fn\s+draw_processing_notifications\b",
            r"^[ \t]*pub\(crate\)\s+fn\s+draw\s*\(",
            r"^[ \t]*fn\s+equipment_slot_rects\b",
        ],
        "crates/haven_game/src/station_interaction_runtime.rs": [
            r"^[ \t]*pub\(super\)\s+fn\s+draw_station_interaction_prompt\b",
        ],
        "crates/haven_game/src/station_placement_runtime.rs": [
            r"^[ \t]*pub\(super\)\s+fn\s+draw_station_placement_preview\b",
            r"^[ \t]*pub\(super\)\s+fn\s+draw_placed_crafting_stations\b",
            r"^[ \t]*fn\s+draw_station_symbol\b",
        ],
    }
    for relative, patterns in targets.items():
        original = read(relative, required=False)
        if original is None:
            continue
        updated = original
        for pattern in patterns:
            updated, _ = add_allow_before_item(updated, pattern)
        write_if_changed(relative, original, updated, changes)


def validate_final_surface() -> None:
    failures: list[str] = []

    main = read("crates/haven_game/src/main.rs") or ""
    bootstrap = read("crates/haven_game/src/game_bootstrap.rs") or ""
    for field in (
        "actor_render_scratch",
        "runtime_diagnostics_cache",
        "runtime_diagnostics_next_refresh_at",
    ):
        if re.search(rf"(?m)^\s*{field}\s*:", main):
            failures.append(f"main.rs: dormant field remains: {field}")
        if re.search(rf"(?m)^\s*{field}\s*:", bootstrap):
            failures.append(f"game_bootstrap.rs: dormant initializer remains: {field}")

    model = read("crates/haven_game/src/character_creator_model.rs") or ""
    if re.search(r"\bfn\s+ordinal\s*\(", model):
        failures.append("character_creator_model.rs: unused ordinal helper remains")
    test_match = re.search(r"(?m)^#\[cfg\(test\)\]", model)
    impl_match = re.search(r"(?m)^impl\s+HeadwearKind\s*\{", model)
    if test_match and impl_match and impl_match.start() > test_match.start():
        failures.append("character_creator_model.rs: HeadwearKind impl remains after tests")

    frontend = read("crates/haven_game/src/client_character_frontend_draw.rs") or ""
    for name in (
        "title_art_rect",
        "draw_title_art",
        "title_source_rect",
        "title_banner_rect",
        "title_menu_layout",
        "draw_title_banner",
        "draw_title_menu_button_image",
        "TITLE_SOURCE_W",
        "TITLE_SOURCE_H",
    ):
        if re.search(rf"\b{re.escape(name)}\b", frontend):
            failures.append(f"client_character_frontend_draw.rs: superseded item remains: {name}")

    compositor = read("crates/haven_game/src/character_runtime_compositor.rs") or ""
    if ".or_else(|| layer.idle_texture.as_ref())" in compositor:
        failures.append("character_runtime_compositor.rs: lazy Option fallback remains")

    save_generation = read("crates/haven_game/src/client_save_generation.rs") or ""
    if re.search(r"let\s+mut\s+settings\s*=\s*WorldCreationSettings::default\(\);", save_generation):
        failures.append("client_save_generation.rs: field-reassign-with-default remains")
    wizard = read("crates/haven_game/src/world_creation_wizard.rs") or ""
    if re.search(r"let\s+mut\s+settings\s*=\s*WorldCreationSettings::default\(\);", wizard):
        failures.append("world_creation_wizard.rs: field-reassign-with-default remains")

    if failures:
        raise SystemExit("Haven game Clippy surface repair failed:\n- " + "\n- ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="repository root override used by validation fixtures")
    args = parser.parse_args()
    global ROOT
    if args.root is not None:
        ROOT = args.root.resolve()

    changes: list[str] = []
    repair_game_scratch_fields(changes)
    repair_creator_surface(changes)
    repair_superseded_title_art(changes)
    repair_compositor_clippy(changes)
    repair_default_initializers(changes)
    repair_staged_ui_lints(changes)
    validate_final_surface()

    if changes:
        print(f"Applied {REVISION} to {len(changes)} source file(s):")
        for relative in changes:
            print(f"  - {relative}")
    else:
        print(f"Haven game Clippy surface already matches {REVISION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
