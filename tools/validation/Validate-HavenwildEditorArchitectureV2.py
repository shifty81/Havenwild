#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

CONTRACTS = {
    "content/editor/architecture/havenwild_editor_command_authority_v2.json": "havenwild.editor_command_authority.v2",
    "content/editor/architecture/havenwild_editor_operations_contract_v2.json": "havenwild.editor_operations_contract.v2",
    "content/editor/architecture/havenwild_editor_core_contract_v2.json": "havenwild.editor_core_contract.v2",
    "content/editor/architecture/havenwild_project_content_authority_v2.json": "havenwild.project_content_authority.v2",
    "content/editor/architecture/havenwild_editor_context_contract_v2.json": "havenwild.editor_context_contract.v2",
    "content/editor/architecture/havenwild_studio_registry_v2.json": "havenwild.studio_registry.v2",
    "content/editor/architecture/havenwild_pie_runtime_bridge_v2.json": "havenwild.pie_runtime_bridge.v2",
    "content/editor/architecture/havenwild_tooling_profile_v2.json": "havenwild.editor_tooling_profile.v2",
}
REQUIRED_SOURCE = [
    "crates/haven_authoring/src/editor_actions.rs",
    "crates/haven_authoring/src/editor_operations.rs",
    "crates/haven_authoring/src/editor_services.rs",
    "crates/haven_authoring/src/project_content.rs",
    "crates/haven_authoring/src/editor_context.rs",
    "crates/haven_authoring/src/studio_registry.rs",
    "crates/haven_authoring/src/play_bridge.rs",
    "apps/haven_editor_native/src/app/command_registry.rs",
]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    errors: list[str] = []
    for rel, schema in CONTRACTS.items():
        path = root / rel
        if not path.is_file():
            errors.append(f"missing editor contract: {rel}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            errors.append(f"invalid JSON {rel}: {exc}")
            continue
        if data.get("schema") != schema:
            errors.append(f"unexpected schema for {rel}: {data.get('schema')!r}")
    for rel in REQUIRED_SOURCE:
        if not (root / rel).is_file():
            errors.append(f"missing editor architecture source: {rel}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    command_adapter = (root / "apps/haven_editor_native/src/app/command_registry.rs").read_text(encoding="utf-8-sig")
    if "haven_authoring::EditorActionId" not in command_adapter:
        errors.append("native command registry still owns a duplicate command enum")
    if "shared_actions_can_appear_on_multiple_menu_surfaces" not in command_adapter:
        errors.append("native menu tests still assume one presentation surface per shared action")
    authoring_lib = (root / "crates/haven_authoring/src/lib.rs").read_text(encoding="utf-8-sig")
    for module in [
        "editor_actions", "editor_operations", "editor_services", "project_content",
        "editor_context", "studio_registry", "play_bridge"
    ]:
        if f"pub mod {module};" not in authoring_lib:
            errors.append(f"haven_authoring does not publish module: {module}")
    action_source = (root / "crates/haven_authoring/src/editor_actions.rs").read_text(encoding="utf-8-sig")
    keys = re.findall(r'=>\s*"([a-z0-9_.-]+)"', action_source)
    if len(keys) != len(set(keys)):
        errors.append("shared editor action stable keys are not unique")
    studio = json.loads((root / "content/editor/architecture/havenwild_studio_registry_v2.json").read_text(encoding="utf-8-sig"))
    if "TileSet / Atlas Mapper Studio" not in studio.get("studios", []):
        errors.append("Atlas Mapper was not normalized into the integrated studio registry")
    pie = json.loads((root / "content/editor/architecture/havenwild_pie_runtime_bridge_v2.json").read_text(encoding="utf-8-sig"))
    if not pie.get("rules", {}).get("playFromHereNeverSilentlyDegradesToPlay"):
        errors.append("PIE contract permits silent Play From Here degradation")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS Havenwild Experimental Editor Architecture v2")
    print("- shared editor command identity")
    print("- normalized jobs/problems contract")
    print("- explicit editor core service ownership")
    print("- shared project content and document/selection context")
    print("- Atlas Mapper represented as integrated Studio")
    print("- explicit PIE/Play From Here request contract")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
