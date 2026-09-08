#!/usr/bin/env python3
"""Materialize the deterministic ULPC Character Conformance Lab case descriptor."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "content/characters/universal_lpc_character_conformance_lab_v1.json"
RUNTIME = ROOT / "content/characters/universal_lpc_runtime_contract_v1.json"
SEEDS = ROOT / "content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json"
OUT = ROOT / "WORKSPACE/generated/universal_lpc_character_conformance_lab_v1.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    spec, runtime, seeds = load(SPEC), load(RUNTIME), load(SEEDS)
    cases = []
    for body in runtime["bodyTypes"]:
        for animation in runtime["animations"]:
            rows = ["north","west","south","east"] if animation["directionRows"] == 4 else ["shared"]
            for direction in rows:
                cases.append({"kind":"character_animation", "bodyType":body, "animation":animation["id"], "direction":direction})
    for item in seeds["items"]:
        cases.append({
            "kind":"gameplay_equipment",
            "itemId":item["itemId"],
            "displayName":item["displayName"],
            "category":item["category"],
            "gameplayAction":item["gameplayAction"],
        })
    payload = {
        "schema":"havenwild.universal_lpc_character_conformance_lab.generated.v1",
        "seed":spec["seed"],
        "sourceSpec":str(SPEC.relative_to(ROOT)).replace("\\","/"),
        "caseCount":len(cases),
        "districts":spec["districts"],
        "cases":cases,
        "editorPresentation":{
            "workspace":"Character Studio / Validation",
            "worldEditorIntegration":"Generated cases are available as a deterministic developer-world descriptor; World/Scene materialization uses the existing editor test-world pipeline rather than a second character editor.",
            "selectFailureOpensExactCase":True
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
    print(f"PASS: generated ULPC Character Conformance Lab descriptor with {len(cases)} cases")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
