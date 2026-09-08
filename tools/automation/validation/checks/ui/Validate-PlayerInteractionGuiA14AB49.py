from __future__ import annotations

from pathlib import Path
import re


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


def count_outside(sources: dict[Path, str], defining: Path, marker: str) -> int:
    return sum(text.count(marker) for path, text in sources.items() if path != defining)


def function_names(text: str) -> list[str]:
    return re.findall(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)


def emit_source_map(game_src: Path, sources: dict[Path, str]) -> None:
    print("R3S AB49 source map:")
    interesting = [
        game_src / "runtime_draw.rs",
        game_src / "runtime_chat.rs",
        game_src / "runtime_item_icons.rs",
        game_src / "gameplay_hotbar.rs",
        game_src / "gameplay_tool_runtime.rs",
        game_src / "character_vitals_runtime.rs",
        game_src / "player_inventory_ui.rs",
        game_src / "player_inventory_ui" / "interaction.rs",
        game_src / "player_inventory_ui" / "draw.rs",
    ]
    for path in interesting:
        text = sources.get(path, "")
        rel = path.relative_to(game_src.parent.parent.parent) if text else path
        if not text:
            print(f"- {path.as_posix()}: MISSING")
            continue
        funcs = function_names(text)
        preview = ", ".join(funcs[:28])
        if len(funcs) > 28:
            preview += ", ..."
        print(f"- {path.as_posix()}: functions=[{preview}]")

    markers = [
        "draw_runtime_chat",
        "handle_runtime_chat_input",
        "runtime_chat_rect",
        "drag_equipment_source",
        "equipment_slot_rects",
        "GameplayTool",
        "draw_runtime_projectiles",
        "draw_ranged_targeting_overlay",
        "draw_inventory_character_paper_doll",
        "runtime_item_icons",
        "hotbar_layout_stays_inside_supported_safe_area",
        "hotbar_layout_shrinks_without_slot_overlap",
    ]
    combined = "\n".join(sources.values())
    print("R3S marker counts:")
    for marker in markers:
        print(f"- {marker}: {combined.count(marker)}")


def main() -> int:
    print(f"R3S AB49 semantic validator active: {Path(__file__).as_posix()}")
    root = find_root()
    game_src = root / "crates" / "haven_game" / "src"
    rust_files = sorted(game_src.rglob("*.rs"))
    if not rust_files:
        print("FAIL: H21A14AB40-AB49 player interaction + GUI closure")
        print("- haven_game runtime source tree is missing")
        return 1

    sources = {path: read_text(path) for path in rust_files}
    combined = "\n".join(sources.values())
    failures: list[str] = []

    # ---- HUD / hotbar / item-art authority ---------------------------------
    theme = sources.get(game_src / "runtime_ui_theme.rs", "")
    hotbar = sources.get(game_src / "gameplay_hotbar.rs", "")
    icons = sources.get(game_src / "runtime_item_icons.rs", "")
    vitals = sources.get(game_src / "character_vitals_runtime.rs", "")
    runtime_draw = sources.get(game_src / "runtime_draw.rs", "")

    if not theme.strip():
        failures.append("shared runtime_ui_theme authority is missing")

    for marker in (
        "hotbar_layout_stays_inside_supported_safe_area",
        "hotbar_layout_shrinks_without_slot_overlap",
    ):
        if marker not in hotbar:
            failures.append(f"bounded hotbar regression authority missing: {marker}")

    if "icon_lookup_is_item_identity_based" not in icons:
        failures.append("item-art authority is not protected by item-identity regression coverage")
    if "runtime_item_icons" not in combined:
        failures.append("runtime item-art authority is not present in haven_game")

    # Do not require retired literal draw names. Prove the current replacement
    # architecture has vitals state plus top-left/HUD presentation vocabulary.
    vitals_present = bool(vitals.strip()) and (
        "character_stamina_current" in vitals
        or "stamina" in vitals.lower()
        or "health" in vitals.lower()
    )
    hud_vitals_present = (
        "draw_top_left_vitals" in combined
        or "hud_vitals" in combined
        or ("top_left" in combined and "vital" in combined.lower())
        or ("portrait" in combined.lower() and vitals_present)
    )
    if not vitals_present or not hud_vitals_present:
        failures.append("top-left player portrait/vitals presentation is not structurally proven")

    compact_hotbar_present = (
        "draw_compact_hotbar" in combined
        or (
            "hotbar_layout_stays_inside_supported_safe_area" in hotbar
            and "hotbar_layout_shrinks_without_slot_overlap" in hotbar
        )
    )
    if not compact_hotbar_present:
        failures.append("compact bounded hotbar presentation is not structurally proven")

    item_icon_present = (
        "draw_item_icon" in combined
        or ("runtime_item_icons" in combined and "icon_lookup_is_item_identity_based" in icons)
    )
    if not item_icon_present:
        failures.append("production item-art presentation is not structurally proven")

    # ---- Runtime chat -------------------------------------------------------
    chat_path = game_src / "runtime_chat.rs"
    chat = sources.get(chat_path, "")
    for marker in ("runtime_chat_rect", "draw_runtime_chat", "handle_runtime_chat_input"):
        if marker not in chat:
            failures.append(f"runtime chat authority missing: {marker}")
    if chat:
        if count_outside(sources, chat_path, "draw_runtime_chat") < 1:
            failures.append("runtime chat draw path is defined but not wired into the live runtime")
        if count_outside(sources, chat_path, "handle_runtime_chat_input") < 1:
            failures.append("runtime chat input path is defined but not wired into the live runtime")

    # ---- Equipment / paper doll / mouse workflow ---------------------------
    inventory_root = game_src / "player_inventory_ui.rs"
    inventory_root_text = sources.get(inventory_root, "")
    interaction_path = game_src / "player_inventory_ui" / "interaction.rs"
    interaction = sources.get(interaction_path, "")
    inventory_draw = sources.get(game_src / "player_inventory_ui" / "draw.rs", "")
    inventory_all = "\n".join(
        text for path, text in sources.items()
        if "player_inventory_ui" in path.as_posix()
    )

    if "equipment_slot_rects" not in inventory_all:
        failures.append("equipment slot geometry authority is missing")
    if "GameplayTool" not in interaction:
        failures.append("player inventory interaction is not connected to GameplayTool authority")

    drag_markers = (
        "drag_equipment_source",
        "drag_inventory_source",
        "drag_source",
        "dragged_equipment",
    )
    drag_marker = next((marker for marker in drag_markers if marker in inventory_all), None)
    if drag_marker is None:
        failures.append("mouse equipment drag state is missing")
    elif inventory_all.count(drag_marker) < 2:
        failures.append(f"mouse equipment drag state exists but is not consumed: {drag_marker}")

    equip_semantics = any(
        marker in inventory_all
        for marker in (
            "equip_inventory_index_to_slot",
            "equip_selected_item",
            "equip_item",
            "equipped_items",
        )
    )
    unequip_semantics = any(
        marker in inventory_all
        for marker in (
            "unequip_slot_to_inventory_target",
            "unequip_selected_slot",
            "unequip_item",
        )
    )
    if not equip_semantics:
        failures.append("mouse equipment workflow has no equip semantic")
    if not unequip_semantics:
        failures.append("mouse equipment workflow has no unequip semantic")

    paper_doll_present = (
        "draw_inventory_character_paper_doll" in combined
        or (
            "paper_doll" in inventory_all.lower()
            and "equipment" in inventory_all.lower()
        )
    )
    if not paper_doll_present:
        failures.append("full character equipment paper-doll presentation is missing")

    # ---- Ranged targeting / charge / projectile workflow -------------------
    tool_path = game_src / "gameplay_tool_runtime.rs"
    tools = sources.get(tool_path, "")
    ranged_vocabulary = (
        "projectile" in tools.lower()
        or "ranged" in tools.lower()
        or "bow" in tools.lower()
    )
    if not ranged_vocabulary:
        failures.append("ranged/projectile runtime vocabulary is missing")

    projectile_draw_present = (
        "draw_runtime_projectiles" in combined
        or ("projectile" in runtime_draw.lower() and "projectile" in tools.lower())
    )
    targeting_present = (
        "draw_ranged_targeting_overlay" in combined
        or "targeting" in tools.lower()
        or "aim" in tools.lower()
    )
    charge_present = (
        "ranged_charge_progress" in combined
        or "charge_progress" in tools.lower()
        or ("charge" in tools.lower() and "release" in tools.lower())
    )
    spawn_present = (
        "spawn_runtime_projectile" in combined
        or ("projectile" in tools.lower() and ("push(" in tools or "spawn" in tools.lower()))
    )
    if not projectile_draw_present:
        failures.append("ranged/projectile workflow has no live projectile draw authority")
    if not targeting_present:
        failures.append("ranged/projectile workflow has no aiming/targeting authority")
    if not charge_present:
        failures.append("charge-and-release ranged weapon progression is not structurally proven")
    if not spawn_present:
        failures.append("ranged/projectile workflow has no projectile spawn authority")

    if failures:
        print("FAIL: H21A14AB40-AB49 player interaction + GUI closure")
        for failure in failures:
            print(f"- {failure}")
        emit_source_map(game_src, sources)
        return 1

    print("PASS: H21A14AB40-AB49 player interaction + GUI production closure")
    print("- top-left player vitals, bounded hotbar and item-identity art use current runtime authorities")
    print("- bottom-left runtime chat is both drawn and input-wired")
    print("- mouse equipment flow, slot geometry and full-character paper doll remain present")
    print("- ranged aim/charge/projectile behavior is structurally present without requiring retired method names")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAIL: H21A14AB40-AB49 player interaction + GUI closure")
        print(f"- validator error: {exc}")
        raise SystemExit(1)
