#!/usr/bin/env python3
"""Validate the behavior-neutral Editor Workflow Gap Audit 02 artifacts."""
from __future__ import annotations
import json
from pathlib import Path

MATRIX = Path("content/editor/architecture/editor_workflow_gap_matrix_v0_1.json")
WORKFLOW = Path("docs/architecture/HAVENWILD_GAME_CANVAS_WORKFLOW_V2.md")
TARGET = Path("docs/architecture/HAVENWILD_EDITOR_AUTHORING_V2_TARGET.md")
ALLOWED_PRIORITY = {"P0", "P1", "P2"}
ALLOWED_STATUS = {"present", "partial", "missing", "legacy_conflict", "blocked"}
REQUIRED_NOUNS = {"SourceSheet", "TileSet", "Material", "Asset", "EntityDefinition", "Instance", "Prefab", "Brush", "Rule"}

def main() -> int:
    failures: list[str] = []
    for path in (MATRIX, WORKFLOW, TARGET):
        if not path.exists():
            failures.append(f"missing {path}")
    if failures:
        print("EDITOR WORKFLOW GAP AUDIT: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    if data.get("schema") != "havenwild.editor_workflow_gap_matrix.v0_1":
        failures.append("unsupported gap matrix schema")
    if data.get("behaviorChange") is not False:
        failures.append("audit pass must remain behavior-neutral")
    nouns = set(data.get("canonicalNouns", []))
    if nouns != REQUIRED_NOUNS:
        failures.append(f"canonical nouns mismatch: {sorted(nouns)}")
    decisions = data.get("lockedDecisions", {})
    if decisions.get("spawnTool") is not False or decisions.get("spawnWindow") is not False:
        failures.append("spawn must remain ordinary contextual entity placement")
    if "unique EntityDefinition" not in decisions.get("playerStart", ""):
        failures.append("Player Start unique EntityDefinition decision missing")
    if "ephemeral" not in decisions.get("playFromHere", ""):
        failures.append("Play From Here ephemeral decision missing")

    gaps = data.get("gaps", [])
    ids = [gap.get("id") for gap in gaps]
    if len(ids) != len(set(ids)):
        failures.append("duplicate gap IDs")
    if len(gaps) < 40:
        failures.append(f"gap matrix unexpectedly small: {len(gaps)}")
    for gap in gaps:
        if gap.get("priority") not in ALLOWED_PRIORITY:
            failures.append(f"invalid priority for {gap.get('id')}")
        if gap.get("status") not in ALLOWED_STATUS:
            failures.append(f"invalid status for {gap.get('id')}")
        if not gap.get("target"):
            failures.append(f"missing target for {gap.get('id')}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    target = TARGET.read_text(encoding="utf-8")
    required_phrases = [
        "There is no separate Spawn tool or Spawn window",
        "Play From Here",
        "Connect",
        "Path",
        "Exact/Manual",
        "Create Prefab",
        "F3 toggles a lightweight",
    ]
    for phrase in required_phrases:
        if phrase not in workflow:
            failures.append(f"workflow contract missing phrase: {phrase}")
    if "no separate Spawn tool or Spawn UI" not in target:
        failures.append("target contract did not correct spawn UI wording")

    if failures:
        print("EDITOR WORKFLOW GAP AUDIT: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    priorities = {p: sum(1 for gap in gaps if gap["priority"] == p) for p in sorted(ALLOWED_PRIORITY)}
    statuses = {s: sum(1 for gap in gaps if gap["status"] == s) for s in sorted(ALLOWED_STATUS)}
    print("EDITOR WORKFLOW GAP AUDIT: PASS")
    print(f" gaps: {len(gaps)}")
    print(" priorities:", ", ".join(f"{k}={v}" for k, v in priorities.items()))
    print(" statuses:", ", ".join(f"{k}={v}" for k, v in statuses.items()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
