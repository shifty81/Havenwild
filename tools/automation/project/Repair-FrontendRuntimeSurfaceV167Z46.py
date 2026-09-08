#!/usr/bin/env python3
"""Repair the partial Pass 167Z40 frontend/runtime integration without replacing baseline-owned files.

This migration is intentionally idempotent.  It patches only the missing API surfaces
reported by the Windows Cargo build and leaves all unrelated source text untouched.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVISION = "167Z47-frontend-runtime-rust-type-repair-v1"


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required source file missing: {relative}")
    return path.read_text(encoding="utf-8")


def write_if_changed(relative: str, original: str, updated: str, changes: list[str]) -> None:
    if updated == original:
        return
    path = ROOT / relative
    path.write_text(updated, encoding="utf-8", newline="\n")
    changes.append(relative)


def matching_paren(text: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unbalanced call beginning at byte {open_index}")


def top_level_argument_count(arguments: str) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    parts: list[str] = []
    start = 0
    for index, char in enumerate(arguments):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(arguments[start:index])
            start = index + 1
    parts.append(arguments[start:])
    return sum(1 for part in parts if part.strip())


def repair_main_menu_rects(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_character_frontend_draw.rs"
    original = read(relative)
    updated = original
    if "pub(crate) fn main_new_rect" not in updated:
        updated += """

// Pass 167Z46: canonical main-menu hit regions shared by draw and input.
pub(crate) fn main_new_rect() -> Rect {
    Rect::new(screen_width() * 0.5 - 150.0, 260.0, 300.0, 58.0)
}

pub(crate) fn main_load_rect() -> Rect {
    Rect::new(screen_width() * 0.5 - 150.0, 334.0, 300.0, 58.0)
}

pub(crate) fn main_quit_rect() -> Rect {
    Rect::new(screen_width() * 0.5 - 150.0, 408.0, 300.0, 48.0)
}
"""
    write_if_changed(relative, original, updated, changes)


def human_label(name: str) -> str:
    known = {
        "None": "None",
        "Hat": "Simple hat",
        "Hood": "Hood",
        "Cap": "Cap",
        "Helmet": "Helmet",
        "Crown": "Crown",
        "Headband": "Headband",
    }
    if name in known:
        return known[name]
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name)


def repair_headwear_helpers(changes: list[str]) -> None:
    relative = "crates/haven_game/src/character_creator_model.rs"
    original = read(relative)
    updated = original
    # Macro-authored enums already receive label/cycle methods from cycle_enum!.
    if "cycle_enum!(HeadwearKind" in updated:
        return

    # Rust nested const items cannot refer to the outer impl through `Self`.
    # Repair an earlier generated helper before deciding whether methods are missing.
    updated = re.sub(
        r"(const\s+VALUES\s*:\s*&\[HeadwearKind\]\s*=\s*&\[)(?P<values>.*?)(\];)",
        lambda match: match.group(1)
        + match.group("values").replace("Self::", "HeadwearKind::")
        + match.group(3),
        updated,
        flags=re.S,
    )

    enum_match = re.search(r"(?:pub\(crate\)\s+)?enum\s+HeadwearKind\s*\{(?P<body>.*?)\}", updated, re.S)
    if not enum_match:
        raise ValueError("HeadwearKind enum was not found")
    body = re.sub(r"//.*", "", enum_match.group("body"))
    variants: list[str] = []
    for raw in body.split(","):
        token = raw.strip()
        if not token:
            continue
        token = re.sub(r"#\s*\[[^\]]*\]", "", token).strip()
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", token)
        if match:
            variants.append(match.group(1))
    if not variants:
        raise ValueError("HeadwearKind contains no variants")
    impl_blocks = "\n".join(
        match.group(0)
        for match in re.finditer(r"impl\s+HeadwearKind\s*\{.*?\n\}", updated, re.S)
    )
    missing_label = "fn label" not in impl_blocks
    missing_cycle = "fn cycle" not in impl_blocks
    if not (missing_label or missing_cycle):
        write_if_changed(relative, original, updated, changes)
        return
    methods: list[str] = []
    if missing_label:
        arms = "\n".join(
            f'            Self::{variant} => "{human_label(variant)}",' for variant in variants
        )
        methods.append(
            "    pub(crate) fn label(self) -> &'static str {\n"
            "        match self {\n"
            f"{arms}\n"
            "        }\n"
            "    }"
        )
    if missing_cycle:
        values = ", ".join(f"HeadwearKind::{variant}" for variant in variants)
        methods.append(
            "    pub(crate) fn cycle(self, delta: isize) -> Self {\n"
            f"        const VALUES: &[HeadwearKind] = &[{values}];\n"
            "        let index = VALUES.iter().position(|value| *value == self).unwrap_or(0);\n"
            "        VALUES[((index as isize + delta).rem_euclid(VALUES.len() as isize)) as usize]\n"
            "    }"
        )
    updated += "\n\n// Pass 167Z46: restore creator helpers expected by the active frontend.\nimpl HeadwearKind {\n"
    updated += "\n\n".join(methods)
    updated += "\n}\n"
    write_if_changed(relative, original, updated, changes)


def repair_frontend_music_lifecycle(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_frontend.rs"
    original = read(relative)
    updated = original
    missing_start = "fn start_frontend_music" not in updated
    missing_stop = "fn stop_frontend_music" not in updated
    if missing_start or missing_stop:
        methods: list[str] = []
        if missing_start:
            methods.append(
                "    pub(crate) fn start_frontend_music(&mut self) {\n"
                "        // The frontend owns the lifecycle hook. Audio binding remains optional\n"
                "        // until a licensed title-music asset is present in the runtime catalog.\n"
                "    }"
            )
        if missing_stop:
            methods.append(
                "    pub(crate) fn stop_frontend_music(&mut self) {\n"
                "        // Paired lifecycle hook; intentionally safe when no music source is bound.\n"
                "    }"
            )
        updated += "\n\n// Pass 167Z46: keep client-entry audio lifecycle calls source-compatible.\nimpl ClientFrontend {\n"
        updated += "\n\n".join(methods)
        updated += "\n}\n"
    write_if_changed(relative, original, updated, changes)


def repair_hud_portrait_call(changes: list[str]) -> None:
    relative = "crates/haven_game/src/runtime_hud.rs"
    original = read(relative)
    updated = original

    needle = "RuntimeCharacterAppearance::frame("
    cursor = 0
    chunks: list[str] = []
    while True:
        index = updated.find(needle, cursor)
        if index < 0:
            break
        open_index = index + len(needle) - 1
        close_index = matching_paren(updated, open_index)
        arguments = updated[open_index + 1 : close_index]
        if top_level_argument_count(arguments) == 3:
            insertion = arguments.rstrip()
            if insertion.endswith(","):
                insertion += "\n                None,\n                0.0,\n            "
            else:
                insertion += ", None, 0.0"
            updated = updated[: open_index + 1] + insertion + updated[close_index:]
            cursor = open_index + 1 + len(insertion) + 1
        else:
            cursor = close_index + 1

    call = "appearance.draw_portrait("
    cursor = 0
    while True:
        index = updated.find(call, cursor)
        if index < 0:
            break
        open_index = index + len(call) - 1
        close_index = matching_paren(updated, open_index)
        replacement = (
            "appearance.draw_portrait(\n"
            "                Rect::new(18.0, screen_height() - 102.0, 76.0, 76.0),\n"
            "                frame,\n"
            "            )"
        )
        updated = updated[:index] + replacement + updated[close_index + 1 :]
        cursor = index + len(replacement)

    write_if_changed(relative, original, updated, changes)


def repair_compositor_numeric_types(changes: list[str]) -> None:
    relative = "crates/haven_game/src/character_runtime_compositor.rs"
    original = read(relative)
    updated = original
    updated = re.sub(
        r"let\s+crop_height\s*=\s*if\s+source\.h\s*>=\s*LPC_FRAME_HEIGHT",
        "let crop_height: f32 = if source.h >= LPC_FRAME_HEIGHT",
        updated,
    )
    write_if_changed(relative, original, updated, changes)


def validate_final_surface() -> None:
    checks = {
        "crates/haven_game/src/client_character_frontend_draw.rs": [
            "pub(crate) fn main_new_rect",
            "pub(crate) fn main_load_rect",
            "pub(crate) fn main_quit_rect",
        ],
        "crates/haven_game/src/client_frontend.rs": [
            "fn start_frontend_music",
            "fn stop_frontend_music",
        ],
        "crates/haven_game/src/character_runtime_compositor.rs": [
            "pub(crate) fn load_profile_vitals",
            "pub(crate) fn draw_portrait",
        ],
        "crates/haven_save/src/lib.rs": [
            "pub character_links: String",
            'character_links: path_string(root.join("characters"))',
        ],
    }
    failures: list[str] = []
    for relative, needles in checks.items():
        source = read(relative)
        for needle in needles:
            if needle not in source:
                failures.append(f"{relative}: missing {needle}")
    hud = read("crates/haven_game/src/runtime_hud.rs")
    if "appearance.draw_portrait(" in hud and "Rect::new(18.0, screen_height() - 102.0, 76.0, 76.0)" not in hud:
        failures.append("runtime_hud.rs: portrait call was not normalized")
    model = read("crates/haven_game/src/character_creator_model.rs")
    if "cycle_enum!(HeadwearKind" not in model:
        if "impl HeadwearKind" not in model or "fn label" not in model or "fn cycle" not in model:
            failures.append("character_creator_model.rs: HeadwearKind helpers remain incomplete")
        if re.search(r"const\s+VALUES\s*:\s*&\[HeadwearKind\].*?Self::", model, re.S):
            failures.append("character_creator_model.rs: nested HeadwearKind const still uses Self")
    compositor = read("crates/haven_game/src/character_runtime_compositor.rs")
    if "let crop_height = if source.h >= LPC_FRAME_HEIGHT" in compositor:
        failures.append("character_runtime_compositor.rs: crop_height remains numerically ambiguous")
    if failures:
        raise SystemExit("Frontend/runtime surface repair failed:\n- " + "\n- ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="repository root override used by validation fixtures")
    args = parser.parse_args()
    global ROOT
    if args.root is not None:
        ROOT = args.root.resolve()
    changes: list[str] = []
    repair_main_menu_rects(changes)
    repair_headwear_helpers(changes)
    repair_frontend_music_lifecycle(changes)
    repair_hud_portrait_call(changes)
    repair_compositor_numeric_types(changes)
    validate_final_surface()
    if changes:
        print(f"Applied {REVISION} to {len(changes)} source file(s):")
        for relative in changes:
            print(f"  - {relative}")
    else:
        print(f"Frontend/runtime surface already matches {REVISION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
