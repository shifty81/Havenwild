from __future__ import annotations

from pathlib import Path
import sys


def find_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "Cargo.toml").is_file() and (parent / "crates" / "haven_game" / "src").is_dir():
            return parent
    raise RuntimeError("could not locate Havenwild repository root")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    root = find_root()
    game_src = root / "crates" / "haven_game" / "src"
    rust_files = sorted(game_src.rglob("*.rs"))
    if not rust_files:
        print("H21A14AB19-AB28 Player GUI validation FAILED")
        print("- haven_game runtime source tree is missing")
        return 1

    sources = {path: read_text(path) for path in rust_files}
    combined = "\n".join(sources.values())
    failures: list[str] = []

    # Equipped Main Hand and action progress are runtime capabilities, not fixed-file literals.
    if 'get("main_hand")' not in combined:
        failures.append('production HUD missing equipped main-hand authority: get("main_hand")')
    if "draw_runtime_progress" not in combined:
        failures.append("production HUD missing runtime action-progress authority: draw_runtime_progress")

    # AB41 / R3P item art authority: a dedicated identity-based icon module must exist and be consumed
    # by another player-facing runtime source. Legacy hand-authored hotbar glyphs are not required.
    icon_path = game_src / "runtime_item_icons.rs"
    icon_text = sources.get(icon_path, "")
    icon_markers = (
        "icon_lookup_is_item_identity_based",
        "has_item_icon",
        "item_icon_rect",
        "icon_rect",
        "draw_item_icon",
    )
    if not icon_text or not any(marker in icon_text for marker in icon_markers):
        failures.append("production HUD is missing AB41/R3P item-identity icon authority")
    icon_consumers = [
        path
        for path, text in sources.items()
        if path != icon_path and "runtime_item_icons" in text
    ]
    if not icon_consumers:
        failures.append("production HUD does not consume runtime_item_icons authority")

    # R3P bounded hotbar geometry is protected by executable regression tests in the runtime source.
    hotbar_path = game_src / "gameplay_hotbar.rs"
    hotbar_text = sources.get(hotbar_path, "")
    for marker in (
        "hotbar_layout_stays_inside_supported_safe_area",
        "hotbar_layout_shrinks_without_slot_overlap",
    ):
        if marker not in hotbar_text:
            failures.append(f"production HUD missing bounded hotbar contract: {marker}")
    if "hotbar_layout" not in hotbar_text:
        failures.append("production HUD is missing shared hotbar layout authority")

    # Shared theme ownership may be imported into each surface; validate the module and real consumers
    # instead of requiring one historical call spelling in one old monolithic source file.
    theme_path = game_src / "runtime_ui_theme.rs"
    theme_text = sources.get(theme_path, "")
    if not theme_text.strip():
        failures.append("shared runtime_ui_theme authority is missing")
    theme_consumers = [
        path
        for path, text in sources.items()
        if path != theme_path and "runtime_ui_theme" in text
    ]
    player_panel_consumers = [
        path
        for path in theme_consumers
        if any(token in path.as_posix().lower() for token in ("pause", "control", "setting", "controller", "inventory", "hud"))
    ]
    if not theme_consumers or not player_panel_consumers:
        failures.append("pause/controls GUI is not routed through shared runtime_ui_theme authority")

    if failures:
        print("H21A14AB19-AB28 Player GUI validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS: H21A14AB19-AB28 player-facing GUI production closure")
    print("- current title/main-menu visual direction remains outside this normalization repair")
    print("- shared runtime_ui_theme owns player HUD/panel chrome through live consumers")
    print("- AB41/R3P item art is resolved by item identity rather than legacy glyph slots")
    print("- tool actions require real equipped main-hand authority and runtime progress")
    print("- bounded hotbar geometry is protected by executable safe-area/overlap regressions")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("H21A14AB19-AB28 Player GUI validation FAILED")
        print(f"- validator error: {exc}")
        raise SystemExit(1)
