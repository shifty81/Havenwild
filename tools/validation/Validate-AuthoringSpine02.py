#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]

errors = []

def require(path: str, needle: str, reason: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle not in text:
        errors.append(f"{path}: {reason} (missing {needle!r})")

def forbid(path: str, needle: str, reason: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle in text:
        errors.append(f"{path}: {reason} (found {needle!r})")

contract_path = ROOT / "content/editor/architecture/authoring_spine_v2.json"
try:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"{contract_path.relative_to(ROOT)}: invalid JSON: {exc}")
    contract = {}

if contract.get("schema") != "havenwild.authoring_spine.v2":
    errors.append("authoring_spine_v2.json: unexpected schema")
if contract.get("pass") != "HW-AUTHORING-SPINE-02":
    errors.append("authoring_spine_v2.json: unexpected pass")

require("crates/haven_authoring/src/lib.rs", "pub mod context;", "context module must be exported")
require("crates/haven_authoring/src/context.rs", "pub struct AuthoringContext", "canonical context missing")
require("crates/haven_authoring/src/context.rs", "RuntimeDeveloperEditor", "runtime editor and lightweight overlay must remain distinct")
require("crates/haven_authoring/src/context.rs", "EntityDefinition", "entity definition must be a normal resource kind")

cap = "crates/haven_authoring/src/capabilities.rs"
require(cap, "PlaceEntity", "entity placement capability missing")
require(cap, "SetPlayerStart", "persistent Player Start capability missing")
require(cap, "pub fn runtime_developer_editor()", "explicit runtime authoring profile missing")

bus = "crates/haven_authoring/src/command_bus.rs"
for command_id in [
    '"world.entity.place"',
    '"world.prefab.place"',
    '"world.brush.apply"',
    '"world.raw_tile_override.place"',
    '"world.player_start.set"',
    '"runtime.play_from_here"',
]:
    require(bus, command_id, f"canonical command ID {command_id} missing")
require(bus, "pub fn execute_transaction(", "canonical apply+history entry point missing")
require(bus, "transaction.apply(world)?;", "canonical executor must apply transaction before recording it")

op = "crates/haven_authoring/src/edit_operation.rs"
require(op, "SetSceneSpawn", "typed Player Start edit operation missing")
require(op, "set_scene_spawn_value(world, scene_id, *before, *after)?;", "Player Start apply path missing")
require(op, "set_scene_spawn_value(world, scene_id, *after, *before)?;", "Player Start revert path missing")
require(op, "outside scene", "Player Start bounds validation missing")

transactions = "crates/haven_authoring/src/transactions.rs"
require(transactions, "pub fn set_scene_spawn(", "Player Start transaction builder missing")
require(transactions, "EditOperation::SetSceneSpawn", "Player Start operation not recorded")

runtime_commands = "crates/haven_game/src/runtime_commands.rs"
require(runtime_commands, ".undo_world(&mut self.world)", "F3 undo must support typed transactions")
require(runtime_commands, ".redo_world(&mut self.world)", "F3 redo must support typed transactions")
require(runtime_commands, "set_active_scene_player_start", "F3 Player Start adapter missing")
require(runtime_commands, ".execute_transaction(&mut self.world, command.clone(), transaction)", "F3 Player Start must execute through canonical command bus")

runtime_input = "crates/haven_game/src/runtime_input.rs"
require(runtime_input, "self.set_active_scene_player_start(GridPos", "F3 P must route through canonical Player Start adapter")
forbid(runtime_input, "scene.spawn_x = self.selected_cell.0;", "F3 must not directly mutate Player Start x")
forbid(runtime_input, "scene.spawn_y = self.selected_cell.1;", "F3 must not directly mutate Player Start y")

if errors:
    print("[FAIL] HW-AUTHORING-SPINE-02")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print("[PASS] HW-AUTHORING-SPINE-02")
print("  canonical context: present")
print("  command IDs/capabilities: present")
print("  typed Player Start transaction: present")
print("  F3 transaction-aware undo/redo: present")
print("  legacy direct F3 spawn mutation: absent")
