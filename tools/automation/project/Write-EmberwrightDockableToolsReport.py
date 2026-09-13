#!/usr/bin/env python3
"""Write a compact report for the Emberwright canvas/dockable-tools pass."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "reports" / "emberwright" / "dockable-tools-15.json"
SOURCES = [
    ROOT / "content" / "editor" / "tool_shell" / "canvas_first_editor_model_v0_1.json",
    ROOT / "content" / "editor" / "tool_shell" / "dockable_tool_panel_contract_v0_1.json",
    ROOT / "content" / "editor" / "tool_shell" / "studio_collapse_plan_v0_1.json",
    ROOT / "content" / "editor" / "tool_shell" / "atlas_assembly_panel_integration_v0_1.json",
    ROOT / "content" / "editor" / "tool_shell" / "room_canvas_tooling_contract_v0_1.json",
    ROOT / "content" / "editor" / "tool_shell" / "tool_panel_migration_inventory_v0_1.json",
]


def main() -> None:
    payload = {
        "schema": "emberwright.dockable_tools_report.v0.1",
        "pass": "HW-EMBERWRIGHT-CANVAS-DOCKABLE-TOOLS-15",
        "status": "source-authored",
        "sources": [],
        "summary": "Canvas is the persistent center; editor tools are configurable dockable/floating panels.",
    }
    for source in SOURCES:
        if not source.exists():
            raise SystemExit(f"missing required source: {source}")
        data = json.loads(source.read_text(encoding="utf-8"))
        payload["sources"].append({"path": str(source.relative_to(ROOT)), "schema": data.get("schema"), "status": data.get("status")})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
