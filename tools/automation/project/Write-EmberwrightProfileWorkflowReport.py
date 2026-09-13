#!/usr/bin/env python3
"""Write a compact Emberwright profile-workflow audit report.

This is intentionally read-only. It verifies the generic profile creation
contract and the Havenwild recreation recipe are present and JSON-loadable.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILES = [
    Path("content/editor/project_profile/generic_profile_creation_contract_v0_1.json"),
    Path("content/editor/project_profile/profile_wizard_steps_v0_1.json"),
    Path("content/editor/project_profile/havenwild_profile_recreation_recipe_v0_1.json"),
    Path("content/editor/architecture/emberwright_genericization_pass_matrix_v0_1.json"),
]
OUT = ROOT / "artifacts" / "reports" / "editor" / "emberwright-profile-workflow-report.json"


def main() -> int:
    report = {
        "schema": "emberwright.profile_workflow_report.v0_1",
        "status": "PASS",
        "files": [],
        "summary": {},
    }
    for relative in FILES:
        path = ROOT / relative
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            report["files"].append({
                "path": str(relative).replace("\\", "/"),
                "schema": payload.get("schema", ""),
                "status": "PASS",
            })
        except Exception as exc:  # pragma: no cover - diagnostic script
            report["status"] = "FAIL"
            report["files"].append({
                "path": str(relative).replace("\\", "/"),
                "status": "FAIL",
                "error": str(exc),
            })
    report["summary"] = {
        "fileCount": len(report["files"]),
        "passCount": sum(1 for item in report["files"] if item["status"] == "PASS"),
        "genericWorkflow": "wizard-driven ProjectProfile creation can recreate the Havenwild profile seed before values migrate out of editor code",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[{report['status']}] wrote {OUT}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
