#!/usr/bin/env python3
"""Write a lightweight Emberwright project-profile audit report.

This is additive scaffolding for the generic editor migration. It does not edit
source; it reads the project-profile policy files and emits a review report.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "content" / "editor" / "project_profile"
OUT = ROOT / "artifacts" / "reports" / "editor" / "emberwright-project-profile-audit.md"


def load(name: str) -> dict:
    path = PROFILE_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schema = load("project_profile_schema_v0_1.json")
    profile = load("havenwild_project_profile_seed_v0_1.json")
    workflow = load("profile_creation_workflow_v0_1.json")
    migration = load("havenwild_specific_value_migration_inventory_v0_1.json")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Emberwright Project Profile Audit",
        "",
        f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Profile: {profile['identity']['displayName']} (`{profile['projectProfileId']}`)",
        f"Schema: {schema['schema']}",
        "",
        "## Enabled workspaces",
    ]
    for workspace in profile["workspaces"]["workspaceOrder"]:
        label = profile["workspaces"]["workspaceLabels"].get(workspace, workspace)
        lines.append(f"- {workspace}: {label}")
    lines.extend(["", "## Generic creation workflow"])
    for step in workflow["workflow"]:
        lines.append(f"- {step['step']}. {step['label']} -> {step['output']}")
    lines.extend(["", "## Migration inventory"])
    for item in migration["items"]:
        examples = ", ".join(item.get("examples", []))
        lines.append(f"- {item['id']} [{item['risk']}] -> {item['target']} ({examples})")
    lines.extend(["", "## Preservation rule", migration["preservationRule"], ""])
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
