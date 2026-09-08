#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def require(path: str) -> Path:
    p = ROOT / path
    if not p.exists():
        errors.append(f"missing {path}")
    return p

contract_path = require("content/assets/world_paint/world_paint_save_load_contract_v0_1.json")
schema_path = require("content/schemas/world_paint_save_load_contract.schema.v0_1.json")
module_path = require("crates/haven_game/src/world_paint_lifecycle.rs")
main_path = require("crates/haven_game/src/main.rs")
persistence_path = require("crates/haven_game/src/runtime_persistence.rs")
input_path = require("crates/haven_game/src/runtime_input.rs")
docs_path = require("docs/assets/WORLD_PAINT_SAVE_LOAD_INTEGRATION_PASS32.md")

if contract_path.exists():
    data = json.loads(contract_path.read_text())
    if data.get("schema") != "havenwild.world_paint_save_load_contract.v0.1":
        errors.append("save/load contract schema id mismatch")
    if data.get("canonicalTileSize") != [32, 32]:
        errors.append("save/load contract must lock canonicalTileSize [32,32]")
    ids = {point.get("id") for point in data.get("integrationPoints", [])}
    for required in ["startup_world_load", "manual_world_load", "worldgen_pack_load", "before_save", "sequence_restore"]:
        if required not in ids:
            errors.append(f"save/load contract missing integration point {required}")
    guards = " ".join(g.get("key", "") for g in data.get("hotkeyRoutingGuards", []))
    for key in ["H", "T", "[ / ]"]:
        if key not in guards:
            errors.append(f"save/load contract missing hotkey guard {key}")

if module_path.exists():
    text = module_path.read_text()
    for token in [
        "world_paint_delta_last_sequence",
        "replay_world_paint_deltas_into_world",
        "replay_paint_deltas_after_world_load",
        "prepare_world_paint_deltas_before_save",
        "load_world_paint_delta_document",
        "load_and_replay_world_paint_deltas",
    ]:
        if token not in text:
            errors.append(f"world_paint_lifecycle.rs missing {token}")
    if len(text.splitlines()) > 220:
        errors.append("world_paint_lifecycle.rs is too large for lifecycle glue")

if main_path.exists():
    text = main_path.read_text()
    for token in [
        "mod world_paint_lifecycle;",
        "world_paint_delta_last_sequence",
        "Startup saved-world paint delta replay",
        "Startup worldgen paint delta replay",
        "Startup starter-world paint delta replay",
    ]:
        if token not in text:
            errors.append(f"main.rs missing {token}")

if persistence_path.exists():
    text = persistence_path.read_text()
    for token in [
        "prepare_world_paint_deltas_before_save",
        "replay_paint_deltas_after_world_load(\"Manual load paint delta replay\")",
        "replay_paint_deltas_after_world_load(\"Worldgen load paint delta replay\")",
    ]:
        if token not in text:
            errors.append(f"runtime_persistence.rs missing {token}")

if input_path.exists():
    text = input_path.read_text()
    guarded = [
        "self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::RightBracket)",
        "self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::LeftBracket)",
        "self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::H)",
        "self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::T)",
    ]
    for token in guarded:
        if token not in text:
            errors.append(f"runtime_input.rs missing Paint-tab hotkey guard: {token}")

if docs_path.exists() and "32x32" not in docs_path.read_text():
    errors.append("Pass 32 docs must mention 32x32 canonical grid")

if errors:
    print("World paint save/load integration validation FAILED:")
    for err in errors:
        print(f" - {err}")
    sys.exit(1)
print("World paint save/load integration validation passed")
