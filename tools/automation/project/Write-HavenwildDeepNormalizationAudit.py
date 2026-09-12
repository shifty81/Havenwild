#!/usr/bin/env python3
"""Emit a lightweight Havenwild normalization audit report from local source files.

This tool is intentionally read-only. It summarizes the policy files added by
HW-DEEP-NORMALIZATION-AUDIT-10 and confirms the expected current-authority files
exist. It does not modify source, generated catalogs, or assets.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POLICY_FILES = [
    "content/assets/asset_authority_reset_policy_v0_1.json",
    "content/validation/validation_tier_policy_v0_1.json",
    "content/editor/gui/editor_gui_normalization_policy_v0_1.json",
    "content/editor/pie/game_canvas_pie_policy_v0_1.json",
    "content/editor/architecture/editor_authoring_v2_implementation_roadmap_v0_2.json",
    "content/build/validator_registry_v4.json",
    "content/build/validation_profiles_v4.json",
    "content/assets/published_world_topology_registry_v1.json",
]

def main() -> int:
    rows = []
    for rel in POLICY_FILES:
        path = ROOT / rel
        exists = path.is_file()
        schema = None
        version = None
        if exists and path.suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                schema = data.get("schema")
                version = data.get("version")
            except Exception as exc:  # read-only report, not gate enforcement
                schema = f"parse error: {exc}"
        rows.append({"path": rel, "exists": exists, "schema": schema, "version": version})
    print(json.dumps({
        "schema": "havenwild.normalization_audit_report.v0_1",
        "root": str(ROOT),
        "policies": rows,
    }, indent=2))
    return 0 if all(row["exists"] for row in rows) else 1

if __name__ == "__main__":
    raise SystemExit(main())
