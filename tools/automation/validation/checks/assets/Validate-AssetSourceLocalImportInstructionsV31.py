#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
checks: list[tuple[str, bool, str]] = []

def check(name: str, condition: bool, detail: str = "") -> None:
    checks.append((name, condition, detail))

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

instructions_path = ROOT / "content/assets/prototype_imports/prototype_asset_local_import_instructions_v0_1.json"
schema_path = ROOT / "content/schemas/asset_local_import_instructions.schema.v0_1.json"
external_path = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
asset_catalog_path = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"

check("instruction manifest exists", instructions_path.exists(), str(instructions_path.relative_to(ROOT)))
check("instruction schema exists", schema_path.exists(), str(schema_path.relative_to(ROOT)))

instructions = json.loads(instructions_path.read_text(encoding="utf-8"))
external = json.loads(external_path.read_text(encoding="utf-8"))
asset_catalog = json.loads(asset_catalog_path.read_text(encoding="utf-8"))

check("instruction schema value", instructions.get("schema") == "havenwild.asset_local_import_instructions.v0_1")
records = instructions.get("records", [])
sources = {source.get("id"): source for source in external.get("sources", [])}
record_ids = {record.get("externalSourceId") for record in records}
check("instruction record count covers external sources", len(records) >= len(sources), f"records={len(records)} sources={len(sources)}")
check("every external source has instructions", set(sources).issubset(record_ids), f"missing={sorted(set(sources) - record_ids)}")

for record in records:
    source_id = record.get("externalSourceId")
    check(f"{source_id} references known source", source_id in sources)
    check(f"{source_id} has workspace path", str(record.get("preferredWorkspaceImportPath", "")).startswith("WORKSPACE/imports/third_party/"), record.get("preferredWorkspaceImportPath", ""))
    check(f"{source_id} has quarantine path", str(record.get("preferredQuarantinePath", "")).startswith("assets/reference_quarantine/third_party/"), record.get("preferredQuarantinePath", ""))
    check(f"{source_id} has input files", bool(record.get("acceptedInputFiles")), str(record.get("acceptedInputFiles")))
    check(f"{source_id} has dry-run command", "DryRun-PrototypeAssetBakeV29.py" in str(record.get("dryRunCommand", "")))
    source = sources.get(source_id, {})
    blocked_policy = (str(source.get("commercialRuntimePolicy", "")) + " " + str(source.get("licenseStatus", ""))).lower()
    if any(token in blocked_policy for token in ["blocked", "non_commercial", "unverified"]):
        check(f"{source_id} blocked source keeps blocked instruction", "blocked" in str(record.get("localImportStatus", "")).lower() or "unverified" in str(record.get("localImportStatus", "")).lower(), record.get("localImportStatus", ""))

catalog_paths = {entry.get("path") for entry in asset_catalog.get("indexes", [])}
check("unified asset catalog indexes instructions", "content/assets/prototype_imports/prototype_asset_local_import_instructions_v0_1.json" in catalog_paths)

assets_lib = read("crates/haven_assets/src/lib.rs")
asset_instructions = read("crates/haven_assets/src/asset_local_import_instructions.rs")
browser = read("crates/haven_game/src/asset_reference_browser_panel.rs")
dryrun = read("tools/automation/assets/DryRun-PrototypeAssetBakeV29.py")
prototype_bake = read("crates/haven_assets/src/prototype_bake.rs")
doc = read("docs/assets/ASSET_SOURCE_LOCAL_IMPORT_INSTRUCTIONS.md")

check("haven_assets exports instruction module", "pub mod asset_local_import_instructions;" in assets_lib)
check("instruction module has loader", "load_asset_local_import_instructions" in asset_instructions)
check("instruction module has index builder", "build_asset_local_import_instruction_index" in asset_instructions)
check("instruction module has lookup", "asset_local_import_instruction_for_source" in asset_instructions)
check("Assets tab imports instructions", "asset_local_import_instructions" in browser)
check("Assets tab has Path button", '"Path"' in browser and "show_asset_reference_import_instruction_status" in browser)
check("Assets tab shows local path", "local path:" in browser)
check("Assets tab shows expected files", "expected:" in browser)
check("Assets tab has I hotkey", "KeyCode::I" in browser)
check("dry-run checks source-specific import folders", "source_slug" in dryrun and "WORKSPACE/imports/third_party/{slug}" in dryrun)
check("Rust dry-run checks source-specific import folders", "fn source_slug" in prototype_bake and "WORKSPACE/imports/third_party/{slug}" in prototype_bake)
check("documentation added", "Asset Source Local Import Instructions" in doc and "WORKSPACE/imports/third_party" in doc)

failed = [item for item in checks if not item[1]]
out_dir = ROOT / "WORKSPACE/generated"
out_dir.mkdir(parents=True, exist_ok=True)
report_lines = ["Asset source local import instructions v0.31 validation", "PASS" if not failed else "FAIL"]
for name, ok, detail in checks:
    report_lines.append(f"{'ok' if ok else 'FAIL'}: {name}{(' - ' + detail) if detail else ''}")
(out_dir / "havenwild_validate_asset_source_local_import_instructions_v31.txt").write_text("\n".join(report_lines), encoding="utf-8")
print("\n".join(report_lines))
if failed:
    raise SystemExit(1)
