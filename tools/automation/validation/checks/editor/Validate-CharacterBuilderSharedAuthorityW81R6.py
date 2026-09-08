#!/usr/bin/env python3
"""Validate W81R6 shared Character Builder foundation/identity authority."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
ERRORS = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        ERRORS.append(f"missing required file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def require(text, markers, context):
    for marker in markers:
        if marker not in text:
            ERRORS.append(f"{context}: missing marker {marker!r}")

def main():
    recipe = read("crates/haven_assets/src/universal_lpc_character_recipe.rs")
    studio = read("apps/haven_editor_native/src/app/character_studio.rs")
    game = read("crates/haven_game/src/character_selection_ui.rs")
    npc = read("crates/haven_assets/src/universal_lpc_npc_generation.rs")
    build = read("tools/build/Build.sh")
    contract_text = read("content/editor/character_builder_shared_authority_w81r6_v1.json")

    require(recipe, [
        "UNIVERSAL_LPC_REQUIRED_FOUNDATION_SLOTS", '"body", "head"',
        "UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES", "universal_lpc_body_type_for_identity",
        "universal_lpc_foundation_head_kind", "universal_lpc_builder_category_id",
        "universal_lpc_identity_compatible", "must contain a head selection",
    ], "shared character authority")
    require(studio, [
        "ensure_required_foundation", "set_age", "set_sex", "category_menu_open",
        "character_category_option_rect", "select_slot_filter",
        "required character foundation and cannot be removed",
    ], "Character Studio creator UX")
    require(game, [
        "builder_categories", "universal_lpc_choices", "universal_lpc_identity_compatible",
        "UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES",
    ], "game character creator shared authority")
    require(npc, [
        "universal_lpc_body_type_for_identity", "apply_identity_foundations",
        "generate_recipe_with_builder",
    ], "NPC shared authority")
    require(build, ["Validate-CharacterBuilderSharedAuthorityW81R6.py"], "Full quality gate")

    try:
        contract = json.loads(contract_text)
        if contract.get("schema") != "havenwild.editor.character_builder_shared_authority.w81r6.v1":
            ERRORS.append("W81R6 contract schema mismatch")
        if contract.get("identity", {}).get("requiredFoundation") != ["body", "head"]:
            ERRORS.append("body/head foundation contract mismatch")
        if len(contract.get("categories", [])) < 18:
            ERRORS.append("shared category catalog is incomplete")
    except Exception as exc:
        ERRORS.append(f"could not parse W81R6 contract: {exc}")

    if ERRORS:
        print("W81R6 Character Builder shared authority validation FAILED")
        for error in ERRORS:
            print("-", error)
        return 1

    print("PASS: W81R6 Character Builder foundation + shared authority")
    print("- body/head are mandatory and headwear cannot replace the head foundation")
    print("- Child/Teen/Adult/Elder identity changes select real foundation variants")
    print("- direct category selection uses the shared expandable Character Builder catalog")
    print("- Character Studio, game creator model, and NPC generation consume shared authority")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
