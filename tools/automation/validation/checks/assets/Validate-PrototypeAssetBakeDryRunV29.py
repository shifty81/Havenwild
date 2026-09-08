#!/usr/bin/env python3
"""Validate prototype asset local bake dry-run wiring.

Pass 23 validator: proves donor/reference packs can be checked by a disabled,
report-only bake stub without copying raw third-party assets or generating
runtime atlases.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PLAN = ROOT / "content/assets/prototype_imports/prototype_asset_local_bake_plan_v0_1.json"
PLAN_SCHEMA = ROOT / "content/schemas/prototype_asset_local_bake_plan.schema.v0_1.json"
SCRIPT = ROOT / "tools/automation/assets/DryRun-PrototypeAssetBakeV29.py"
SCRIPT_PS = ROOT / "tools/automation/assets/DryRun-PrototypeAssetBakeV29.ps1"
REPORT = ROOT / "WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json"
RUST_MODEL = ROOT / "crates/haven_assets/src/prototype_bake.rs"
LIB_RS = ROOT / "crates/haven_assets/src/lib.rs"
DOC = ROOT / "docs/assets/PROTOTYPE_ASSET_LOCAL_BAKE_DRY_RUN.md"
ADAPTER_CATALOG = ROOT / "content/assets/prototype_imports/prototype_asset_import_adapters_v0_1.json"
EXTERNAL = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"

REQUIRED_ADAPTER_IDS = {
    "adapter.pipoya_world_tileset_32.v0_1",
    "adapter.free_pixel_food_icons_32.v0_1",
    "adapter.pixel_mart_icons_32.v0_1",
}
BLOCKED_SOURCE_IDS = {
    "third_party.shubibubi.cozy_farm_free_version",
    "third_party.shubibubi.cozy_interior_free_version",
    "third_party.shubibubi.cozy_town_free_version",
    "third_party.lpc.opengameart_mixed_loose_assets",
    "third_party.fishing_free_noncommercial",
    "third_party.char_free_unverified",
    "third_party.game_endeavor.mystic_woods_free",
}
RAW_NAMES = {
    "Asset Pack.zip",
    "Pipoya RPG Tileset 32x32.zip",
    "Door_Animation.zip",
    "Unorganized Parts.zip",
    "Pipoya RPG World Tileset 48x48 40x40 32x32.zip",
    "Pipoya RPG World Tileset 48x48 40x40 32x32 for Tiled1.5.zip",
    "FreePixelFood.zip",
    "Food.png",
    "Pixel_Mart.zip",
    "fishing_free.zip",
    "char free.zip",
    "mystic_woods_free_2.2.zip",
    "free version.zip",
    "Interior free.zip",
    "town free.zip",
}


def load(path: Path):
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for required in [PLAN, PLAN_SCHEMA, SCRIPT, SCRIPT_PS, RUST_MODEL, DOC, ADAPTER_CATALOG, EXTERNAL]:
        if not required.exists():
            errors.append(f"missing required pass 23 file: {rel(required)}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(" -", error)
        return 1

    plan = load(PLAN)
    load(PLAN_SCHEMA)
    adapter_catalog = load(ADAPTER_CATALOG)
    external = load(EXTERNAL)

    if plan.get("schema") != "havenwild.prototype_asset_local_bake_plan.v0_1":
        errors.append(f"invalid bake plan schema: {plan.get('schema')}")
    if plan.get("enabledByDefault") is not False:
        errors.append("bake plan must be disabled by default")
    if plan.get("dryRunOnly") is not True:
        errors.append("bake plan must be dryRunOnly=true")
    if plan.get("copyRawAssets") is not False:
        errors.append("bake plan must not copy raw assets")
    if plan.get("generateRuntimeAssets") is not False:
        errors.append("bake plan must not generate runtime assets")
    if plan.get("reportPath") != "WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json":
        errors.append(f"unexpected reportPath: {plan.get('reportPath')}")

    plan_adapter_ids = {entry.get("adapterId") for entry in plan.get("entries") or []}
    missing_adapters = REQUIRED_ADAPTER_IDS - plan_adapter_ids
    if missing_adapters:
        errors.append(f"bake plan missing required adapter ids: {sorted(missing_adapters)}")
    adapter_paths = adapter_catalog.get("adapters") or []
    adapter_ids = {load(ROOT / path).get("id") for path in adapter_paths}
    for adapter_id in plan_adapter_ids:
        if adapter_id not in adapter_ids:
            errors.append(f"bake plan references unknown adapter id: {adapter_id}")
    for entry in plan.get("entries") or []:
        if entry.get("allowedOutputMode") != "report_only_no_runtime_assets":
            errors.append(f"{entry.get('id')}: allowedOutputMode must be report_only_no_runtime_assets")

    rust = RUST_MODEL.read_text(encoding="utf-8")
    for needle in [
        "PROTOTYPE_ASSET_LOCAL_BAKE_PLAN_PATH",
        "PrototypeAssetLocalBakePlan",
        "dry_run_prototype_asset_bake",
        "RefusedBlockedSource",
        "MissingSource",
        "copy_raw_assets",
        "generate_runtime_assets",
    ]:
        if needle not in rust:
            errors.append(f"prototype_bake.rs missing expected model/wiring: {needle}")
    lib = LIB_RS.read_text(encoding="utf-8")
    if "pub mod prototype_bake;" not in lib:
        errors.append("haven_assets lib.rs must expose prototype_bake")

    doc = DOC.read_text(encoding="utf-8")
    for needle in ["dry-run", "disabled", "blocked", "no raw", "report"]:
        if needle not in doc.lower():
            errors.append(f"dry-run doc missing phrase: {needle}")

    # Execute the dry-run command. It must succeed even when local source files are missing,
    # because missing availability is reported, not fatal.
    try:
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        errors.append(f"dry-run command failed: {exc}")
    if not REPORT.exists():
        errors.append("dry-run command did not write expected report")
    else:
        report = load(REPORT)
        if report.get("schema") != "havenwild.prototype_asset_bake_dry_run_report.v0_1":
            errors.append(f"invalid dry-run report schema: {report.get('schema')}")
        if report.get("dryRunOnly") is not True:
            errors.append("dry-run report must declare dryRunOnly=true")
        if report.get("copyRawAssets") is not False:
            errors.append("dry-run report must declare copyRawAssets=false")
        if report.get("generateRuntimeAssets") is not False:
            errors.append("dry-run report must declare generateRuntimeAssets=false")
        entries = report.get("entries") or []
        if len(entries) < 3:
            errors.append(f"expected at least 3 dry-run adapter entries, found {len(entries)}")
        seen_report_adapters = {entry.get("adapterId") for entry in entries}
        for adapter_id in REQUIRED_ADAPTER_IDS:
            if adapter_id not in seen_report_adapters:
                errors.append(f"dry-run report missing adapter {adapter_id}")
        allowed_status = {"ready", "missing_source", "refused_blocked_source", "plan_error"}
        for entry in entries:
            if entry.get("status") not in allowed_status:
                errors.append(f"{entry.get('id')} invalid status {entry.get('status')}")
            if entry.get("status") == "ready":
                warnings.append(f"{entry.get('id')} found all local source files; still dry-run only")
            if entry.get("outputProcessedAtlas") and (ROOT / entry.get("outputProcessedAtlas")).exists():
                errors.append(f"dry-run unexpectedly generated processed atlas: {entry.get('outputProcessedAtlas')}")
        probes = report.get("blockedSourceProbes") or []
        probed_ids = {probe.get("sourceId") for probe in probes}
        if not (BLOCKED_SOURCE_IDS & probed_ids):
            errors.append("dry-run report must include at least one refused blocked source probe")
        for probe in probes:
            if probe.get("status") != "refused_blocked_source":
                errors.append(f"blocked source probe not refused: {probe}")

    # Raw uploaded archives/sheets should not be copied into project assets/content as part of the stub.
    for root in [ROOT / "assets/processed", ROOT / "content/assets"]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.name in RAW_NAMES:
                errors.append(f"raw third-party file copied into runtime/catalog tree: {rel(path)}")

    # Blocked sources must remain blocked in the external source registry.
    sources = {source.get("id"): source for source in external.get("sources") or []}
    for sid in BLOCKED_SOURCE_IDS:
        source = sources.get(sid)
        if not source:
            continue
        policy = str(source.get("commercialRuntimePolicy", ""))
        if "blocked" not in policy and "unverified" not in str(source.get("licenseStatus", "")):
            errors.append(f"{sid} must remain blocked/unverified in source registry")
        if source.get("processedPrototypePath"):
            errors.append(f"{sid} must not have processedPrototypePath while blocked")

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(" -", warning)
    if errors:
        print("ERRORS:")
        for error in errors:
            print(" -", error)
        return 1
    report_summary = load(REPORT).get("summary")
    print(f"Validate-PrototypeAssetBakeDryRunV29: OK ({report_summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
