#!/usr/bin/env python3
"""Dry-run Havenwild prototype asset bake availability checks.

This command is intentionally report-only. It checks whether user-supplied or
quarantined donor source archives/sheets are present, refuses blocked sources,
and writes a safe JSON report without copying raw assets or generating runtime
atlases.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
QUEUE = ROOT / "content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json"
ADAPTER_CATALOG = ROOT / "content/assets/prototype_imports/prototype_asset_import_adapters_v0_1.json"
BAKE_PLAN = ROOT / "content/assets/prototype_imports/prototype_asset_local_bake_plan_v0_1.json"
REPORT = ROOT / "WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def is_blocked(source: dict, blocked_tokens: list[str]) -> bool:
    policy = str(source.get("commercialRuntimePolicy", "")).lower()
    license_status = str(source.get("licenseStatus", "")).lower()
    return any(token.lower() in policy or token.lower() in license_status for token in blocked_tokens)


def source_slug(source_id: str) -> str:
    if source_id.startswith("third_party."):
        source_id = source_id[len("third_party."):]
    return source_id.replace(".", "_").replace("-", "_")


def source_candidates(source_id: str, raw_quarantine_path: str, archive_name: str) -> list[str]:
    raw_quarantine_path = raw_quarantine_path.rstrip("/")
    slug = source_slug(source_id)
    return [
        f"WORKSPACE/imports/third_party/{slug}/{archive_name}",
        f"{raw_quarantine_path}/{archive_name}",
        f"WORKSPACE/imports/{archive_name}",
        f"WORKSPACE/imports/third_party/{archive_name}",
    ]


def main() -> int:
    sources_doc = load_json(SOURCES)
    queue_doc = load_json(QUEUE)
    catalog_doc = load_json(ADAPTER_CATALOG)
    plan_doc = load_json(BAKE_PLAN)

    if plan_doc.get("schema") != "havenwild.prototype_asset_local_bake_plan.v0_1":
        raise AssertionError(f"Unsupported bake plan schema: {plan_doc.get('schema')}")
    if plan_doc.get("enabledByDefault") is not False:
        raise AssertionError("Prototype asset local bake must remain disabled by default")
    if plan_doc.get("dryRunOnly") is not True:
        raise AssertionError("Pass 23 bake path must remain dry-run only")
    if plan_doc.get("copyRawAssets") is not False:
        raise AssertionError("Dry-run bake must not copy raw assets")
    if plan_doc.get("generateRuntimeAssets") is not False:
        raise AssertionError("Dry-run bake must not generate runtime assets")

    sources = {source.get("id"): source for source in sources_doc.get("sources") or []}
    adapter_paths = catalog_doc.get("adapters") or []
    adapters: dict[str, dict] = {}
    for adapter_path in adapter_paths:
        adapter = load_json(ROOT / adapter_path)
        adapters[adapter.get("id")] = adapter

    blocked_tokens = list(plan_doc.get("blockedPolicyTokens") or ["blocked", "non_commercial_only", "unverified"])
    report_entries: list[dict] = []
    for entry in plan_doc.get("entries") or []:
        adapter_id = entry.get("adapterId")
        adapter = adapters.get(adapter_id)
        if not adapter:
            report_entries.append({
                "id": entry.get("id"),
                "adapterId": adapter_id,
                "externalSourceId": None,
                "status": "plan_error",
                "inputs": [],
                "outputMetadata": "",
                "outputProcessedAtlas": "",
                "notes": ["missing adapter; no bake attempted"],
            })
            continue
        source_id = adapter.get("externalSourceId")
        source = sources.get(source_id)
        if not source:
            report_entries.append({
                "id": entry.get("id"),
                "adapterId": adapter_id,
                "externalSourceId": source_id,
                "status": "plan_error",
                "inputs": [],
                "outputMetadata": adapter.get("outputPlan", {}).get("metadata", ""),
                "outputProcessedAtlas": adapter.get("outputPlan", {}).get("processedAtlas", ""),
                "notes": ["missing external source; no bake attempted"],
            })
            continue
        if is_blocked(source, blocked_tokens):
            report_entries.append({
                "id": entry.get("id"),
                "adapterId": adapter_id,
                "externalSourceId": source_id,
                "status": "refused_blocked_source",
                "inputs": [],
                "outputMetadata": adapter.get("outputPlan", {}).get("metadata", ""),
                "outputProcessedAtlas": adapter.get("outputPlan", {}).get("processedAtlas", ""),
                "notes": ["blocked source refused before checking inputs"],
            })
            continue

        input_reports: list[dict] = []
        all_found = True
        for source_input in adapter.get("sourceInputs") or []:
            archive_name = source_input.get("archiveName", "")
            checked = source_candidates(source_id, source.get("rawQuarantinePath", ""), archive_name)
            found = any((ROOT / path).exists() for path in checked)
            all_found = all_found and found
            input_reports.append({
                "archiveName": archive_name,
                "role": source_input.get("role", ""),
                "found": found,
                "checkedPaths": checked,
            })
        report_entries.append({
            "id": entry.get("id"),
            "adapterId": adapter_id,
            "externalSourceId": source_id,
            "status": "ready" if all_found else "missing_source",
            "inputs": input_reports,
            "outputMetadata": adapter.get("outputPlan", {}).get("metadata", ""),
            "outputProcessedAtlas": adapter.get("outputPlan", {}).get("processedAtlas", ""),
            "notes": ["dry-run only; no raw assets copied and no runtime atlas generated"],
        })

    blocked_source_probes: list[dict] = []
    if (plan_doc.get("blockedSourceProbePolicy") or {}).get("checkBlockedQueueEntries"):
        for queue_entry in queue_doc.get("entries") or []:
            if "blocked" not in str(queue_entry.get("status", "")):
                continue
            source_id = queue_entry.get("externalSourceId")
            source = sources.get(source_id)
            if not source:
                continue
            blocked_source_probes.append({
                "sourceId": source_id,
                "policy": source.get("commercialRuntimePolicy", ""),
                "status": "refused_blocked_source",
                "reason": "blocked prototype import queue entry refused by dry-run bake gate",
            })

    ready = sum(1 for entry in report_entries if entry.get("status") == "ready")
    missing = sum(1 for entry in report_entries if entry.get("status") == "missing_source")
    refused = len(blocked_source_probes) + sum(1 for entry in report_entries if entry.get("status") == "refused_blocked_source")
    report = {
        "schema": "havenwild.prototype_asset_bake_dry_run_report.v0_1",
        "dryRunOnly": True,
        "copyRawAssets": False,
        "generateRuntimeAssets": False,
        "adapterCatalogPath": rel(ADAPTER_CATALOG),
        "reportPath": rel(REPORT),
        "entries": report_entries,
        "blockedSourceProbes": blocked_source_probes,
        "summary": f"ready={ready}; missing_source={missing}; refused_blocked={refused}",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DryRun-PrototypeAssetBakeV29: wrote {rel(REPORT)}")
    print(report["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
