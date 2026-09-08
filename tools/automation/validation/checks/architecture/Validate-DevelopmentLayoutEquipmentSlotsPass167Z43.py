#!/usr/bin/env python3
"""Validate Pass 167Z43 layout migration and LPC equipment-slot authority."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


def discover_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "tools").is_dir() and (candidate / "content").is_dir():
            return candidate
    raise RuntimeError("could not discover Havenwild repository root")


ROOT = discover_root()
NORMALIZER = ROOT / "tools/automation/project/Normalize-WorkspaceLayout.py"
REQUIRED_STANDARD = {
    "head",
    "face",
    "neck",
    "shoulders",
    "torso",
    "torso_outer",
    "arms",
    "hands",
    "waist",
    "legs",
    "feet",
    "back",
    "main_hand",
    "off_hand",
    "accessory_1",
    "accessory_2",
    "ring_1",
    "ring_2",
    "utility",
}


def load_json(relative: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing required JSON: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_no_legacy_refs(relative: str) -> None:
    text = (ROOT / relative).read_text(encoding="utf-8")
    legacy = "SCRIPTS"
    if legacy + "/" in text or legacy + "\\" in text:
        raise AssertionError(f"{relative} still references the retired root SCRIPTS layout")


def load_normalizer():
    spec = importlib.util.spec_from_file_location("havenwild_layout_normalizer_v167z43", NORMALIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {NORMALIZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_migration_fixture() -> None:
    module = load_normalizer()
    with tempfile.TemporaryDirectory(prefix="havenwild-z43-layout-") as directory:
        fixture = Path(directory)
        (fixture / "SCRIPTS" / "validation").mkdir(parents=True)
        (fixture / "SCRIPTS" / "validation" / "context.py").write_text("VALUE = 1\n", encoding="utf-8")
        (fixture / "SCRIPTS" / "Validate-LpcProjectFoundationPass167Z40.py").write_text(
            "print('legacy validator')\n", encoding="utf-8"
        )
        (fixture / "SCRIPTS" / "UnknownLegacyTool.py").write_text("print('archive me')\n", encoding="utf-8")
        (fixture / "tools/automation/validation/checks/assets").mkdir(parents=True)
        (fixture / "tools/archive").mkdir(parents=True)
        module.ROOT = fixture
        changed = module.normalize_legacy_scripts()
        assert changed is True
        assert not (fixture / "SCRIPTS").exists()
        assert (fixture / "tools/automation/validation/context.py").is_file()
        assert (
            fixture
            / "tools/automation/validation/checks/assets/Validate-LpcProjectFoundationPass167Z40.py"
        ).is_file()
        assert (
            fixture
            / "tools/archive/legacy_scripts/pass167z43_layout_migration/unclassified/UnknownLegacyTool.py"
        ).is_file()


def main() -> int:
    for relative in (
        "content/build/validator_registry_v3.json",
        "content/validation/validation_manifest_v1.json",
        "tools/tool_registry.json",
        "tools/automation/validation/validation_runner.py",
    ):
        require_no_legacy_refs(relative)

    normalizer_text = NORMALIZER.read_text(encoding="utf-8")
    for token in (
        "normalize_legacy_scripts",
        "LEGACY_SCRIPT_ROUTES",
        "tools/archive/legacy_scripts/pass167z43_layout_migration",
    ):
        if token not in normalizer_text:
            raise AssertionError(f"normalizer is missing Z43 migration token: {token}")
    validate_migration_fixture()

    policy = load_json("content/characters/gameplay_character_equipment_policy_v0_1.json")
    contract = load_json("content/characters/character_equipment_slot_contract_v0_1.json")
    menu = load_json("content/ui/character_equipment_menu_v0_1.json")

    slots = policy["slots"]
    ids = [entry["id"] for entry in slots]
    if len(ids) != len(set(ids)):
        raise AssertionError("equipment policy contains duplicate slot IDs")
    if set(ids) != REQUIRED_STANDARD | {"mobility"}:
        raise AssertionError(f"unexpected equipment slot set: {sorted(ids)}")
    if contract["standardSlotCount"] != 19 or contract["conditionalSlotCount"] != 1:
        raise AssertionError("equipment slot counts are not 19 standard plus 1 conditional")
    if contract["pregnancyPolicy"]["equipmentSlot"] is not False:
        raise AssertionError("pregnancy must remain a body state, not an equipment slot")
    if contract["toolPolicy"]["twoHandedToolsOccupy"] != ["main_hand", "off_hand"]:
        raise AssertionError("two-handed tool occupancy is not normalized")
    if [tab["id"] for tab in menu["tabs"]] != ["equipment", "wardrobe", "appearance", "loadouts"]:
        raise AssertionError("equipment menu tabs are not normalized")
    if menu["implementationState"] != "data_and_validation_foundation":
        raise AssertionError("Z43 must not falsely claim completed runtime equipment-screen wiring")

    print("Pass 167Z43 development-layout and equipment-slot contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
