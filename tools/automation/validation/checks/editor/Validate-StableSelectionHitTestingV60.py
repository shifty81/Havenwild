#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


ids = read("crates/haven_core/src/authored_ids.rs")
foundation = read("crates/haven_core/src/foundation.rs")
entities = read("crates/haven_core/src/foundation/authored_entities.rs")
scene_world = read("crates/haven_core/src/foundation/scene_world.rs")
selection = read("crates/haven_authoring/src/selection.rs")
hit_testing = read("crates/haven_authoring/src/hit_testing.rs")
transactions = read("crates/haven_authoring/src/transactions.rs")
scene_edit = read("crates/haven_editor/src/scene_edit.rs")
region_graph = read("crates/haven_world/src/region_graph.rs")
validation_registry = read("crates/haven_editor/src/validation_registry.rs")
native_app = "\n".join(
    read(rel)
    for rel in [
        "apps/haven_editor_native/src/app/mod.rs",
        "apps/haven_editor_native/src/app/selection_controller.rs",
        "apps/haven_editor_native/src/app/scene_authoring.rs",
        "apps/haven_editor_native/src/app/render_helpers.rs",
        "apps/haven_editor_native/src/app/region_commands.rs",
    ]
)
contract_text = read("content/editor/selection/stable_selection_hit_testing_contract_v0_1.json")
read("docs/editor/STABLE_SELECTION_HIT_TESTING_PASS48C.md")

checks = [
    ("numeric_id!(ObjectId", ids, "ObjectId type missing"),
    ("numeric_id!(TransitionId", ids, "TransitionId type missing"),
    ("numeric_id!(ZoneId", ids, "ZoneId type missing"),
    ("pub struct RegionNodeId", ids, "RegionNodeId type missing"),
    ("mod authored_entities;", foundation, "authored entity extraction missing"),
    ("pub id: ObjectId", entities, "PlacedObject has no stable ID"),
    ("pub id: TransitionId", entities, "Transition has no stable ID"),
    ("object.id.code()", foundation, "object IDs are not persisted"),
    ("ObjectId::parse_code", foundation, "object ID line-save loading missing"),
    ("transition.id.code()", scene_world, "transition IDs are not persisted"),
    ("TransitionId::parse_code", scene_world, "transition ID line-save loading missing"),
    ("pub struct EditorSelection", selection, "canonical EditorSelection missing"),
    ("Object(ObjectId)", selection, "object selection is not ID-backed"),
    ("Transition(TransitionId)", selection, "transition selection is not ID-backed"),
    ("RegionNode(RegionNodeId)", selection, "region-node selection is not ID-backed"),
    ("pub struct CanvasHit", hit_testing, "shared CanvasHit missing"),
    ("pub fn hit_test_scene_cell", hit_testing, "shared scene hit-test function missing"),
    ("scene.map.object_id_at", hit_testing, "object hit testing does not resolve stable IDs"),
    ("scene.transition_id_at", hit_testing, "transition hit testing does not resolve stable IDs"),
    ("pub struct EditTransaction", transactions, "typed transaction contract missing"),
    ("pub enum EditOperation", transactions, "typed edit operation contract missing"),
    ("object_id: ObjectId", scene_edit, "scene object edit API still accepts indexes"),
    ("transition_id: TransitionId", scene_edit, "transition edit API still accepts coordinates/indexes"),
    ("pub id: RegionNodeId", region_graph, "region graph node IDs are not stable values"),
    ("selection: EditorSelection", native_app, "native editor does not own canonical selection"),
    ("hit_test_scene_cell", native_app, "native editor does not use shared hit testing"),
    ("primary_object_id", native_app, "native object operations do not resolve stable selection"),
    ("primary_region_node_id", native_app, "native region selection is not stable-ID-backed"),
    ("id: \"stable_selection\"", validation_registry, "editor validation registry omits stable selection"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for forbidden, message in [
    ("selected_scene_object: Option<usize>", "legacy object-index selection remains"),
    ("selected_node: usize", "legacy region-node index selection remains"),
    ("macroquad", "headless hit-testing depends on Macroquad"),
]:
    haystack = native_app if forbidden != "macroquad" else hit_testing
    if forbidden in haystack:
        errors.append(message)

if len(foundation.splitlines()) > 1810:
    errors.append("foundation.rs exceeded the reduced Pass 48C no-growth ceiling")
if len(entities.splitlines()) > 750:
    errors.append("authored_entities.rs exceeds the standard module ceiling")

try:
    contract = json.loads(contract_text)
    identity = contract.get("identity", {})
    if identity.get("objects") != "ObjectId":
        errors.append("selection contract object identity mismatch")
    if identity.get("transitions") != "TransitionId":
        errors.append("selection contract transition identity mismatch")
    if contract.get("selection", {}).get("vectorIndexesForbiddenForPersistentSelection") is not True:
        errors.append("selection contract does not forbid persistent vector-index selection")
    if contract.get("canvasHitTesting", {}).get("owner") != "haven_authoring":
        errors.append("canvas hit-test contract owner mismatch")
    if contract.get("persistence", {}).get("legacyObjectLinesReceiveIds") is not True:
        errors.append("legacy object identity migration is not required")
    if contract.get("transactions", {}).get("executionDeferredTo") != "Pass 48D":
        errors.append("typed transaction handoff mismatch")
except Exception as exc:
    errors.append(f"invalid stable selection contract json: {exc}")

if errors:
    print("Stable selection / shared hit-testing validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Stable selection / shared hit-testing validation passed.")
