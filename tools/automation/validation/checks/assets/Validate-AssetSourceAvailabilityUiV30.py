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

assets_lib = read("crates/haven_assets/src/lib.rs")
source_availability = read("crates/haven_assets/src/asset_source_availability.rs")
prototype_bake = read("crates/haven_assets/src/prototype_bake.rs")
browser = read("crates/haven_game/src/asset_reference_browser_panel.rs")
doc = read("docs/assets/ASSET_SOURCE_AVAILABILITY_UI.md")

check("haven_assets module exported", "pub mod asset_source_availability;" in assets_lib)
check("availability report loader exists", "load_asset_source_availability_report" in source_availability)
check("availability index builder exists", "build_asset_source_availability_index" in source_availability)
check("availability selected lookup exists", "availability_for_donor_record" in source_availability)
check("availability states include ready", "AssetSourceAvailabilityState" in source_availability and "Ready" in source_availability)
check("availability states include missing", "MissingSource" in source_availability)
check("availability states include blocked", "RefusedBlockedSource" in source_availability)
check("prototype bake report is deserializable", "Deserialize, Serialize" in prototype_bake and "PrototypeAssetBakeDryRunReport" in prototype_bake)
check("asset browser imports availability", "asset_source_availability" in browser)
check("asset browser references bake report path", "PROTOTYPE_ASSET_LOCAL_BAKE_REPORT_PATH" in browser)
check("asset browser row shows availability", "availability.state.short_label()" in browser)
check("asset browser detail shows found inputs", "inputs {}/{}" in browser)
check("asset browser detail shows bake note", "bake note:" in browser)
check("availability color function exists", "fn availability_color" in browser)
check("documentation added", "Asset Source Availability UI" in doc)

report_path = ROOT / "WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json"
if report_path.exists():
    report = json.loads(report_path.read_text(encoding="utf-8"))
    statuses = {entry.get("status") for entry in report.get("entries", [])}
    check("dry-run report present", True, str(report_path))
    check("dry-run report has entries", bool(report.get("entries")), str(len(report.get("entries", []))))
    check("dry-run report includes missing/ready statuses", bool(statuses & {"missing_source", "ready"}), str(sorted(statuses)))
else:
    check("dry-run report present", False, str(report_path))

failed = [item for item in checks if not item[1]]
out_dir = ROOT / "WORKSPACE/generated"
out_dir.mkdir(parents=True, exist_ok=True)
report_lines = ["Asset source availability UI v0.30 validation", "PASS" if not failed else "FAIL"]
for name, ok, detail in checks:
    report_lines.append(f"{'ok' if ok else 'FAIL'}: {name}{(' - ' + detail) if detail else ''}")
(out_dir / "havenwild_validate_asset_source_availability_ui_v30.txt").write_text("\n".join(report_lines), encoding="utf-8")
print("\n".join(report_lines))
if failed:
    raise SystemExit(1)
