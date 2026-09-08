#!/usr/bin/env python3
"""Validate Havenwild third-party asset intake manifests.

Pass 19 validator: checks that audited third-party assets are quarantined,
policy-gated, and never silently promoted into runtime output folders.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE_MANIFEST = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
IMPORT_QUEUE = ROOT / "content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json"
POLICY_DOC = ROOT / "docs/assets/THIRD_PARTY_ASSET_INTAKE_POLICY.md"
SCHEMA = ROOT / "content/schemas/external_asset_source.schema.v0_1.json"
QUARANTINE_ROOT = ROOT / "assets/reference_quarantine/third_party"

ALLOWED_SCHEMA = "havenwild.external_asset_sources.v0_1"
QUEUE_SCHEMA = "havenwild.prototype_asset_import_queue.v0_1"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - command-line validator
        raise AssertionError(f"Failed to parse {path.relative_to(ROOT)}: {exc}") from exc


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    sources_doc = load_json(SOURCE_MANIFEST)
    queue_doc = load_json(IMPORT_QUEUE)
    load_json(SCHEMA)

    if sources_doc.get("schema") != ALLOWED_SCHEMA:
        errors.append(f"source manifest schema mismatch: {sources_doc.get('schema')}")
    if queue_doc.get("schema") != QUEUE_SCHEMA:
        errors.append(f"queue manifest schema mismatch: {queue_doc.get('schema')}")
    if not POLICY_DOC.exists():
        errors.append("missing docs/assets/THIRD_PARTY_ASSET_INTAKE_POLICY.md")

    sources = sources_doc.get("sources") or []
    queue_entries = queue_doc.get("entries") or []
    if len(sources) < 8:
        errors.append(f"expected at least 8 audited sources, found {len(sources)}")
    if len(queue_entries) < 4:
        errors.append(f"expected at least 4 prototype import queue entries, found {len(queue_entries)}")

    source_ids: set[str] = set()
    blocked_ids: set[str] = set()
    allowed_ids: set[str] = set()
    required_quarantine_paths: set[str] = set()

    for source in sources:
        sid = source.get("id")
        if not sid:
            errors.append("source missing id")
            continue
        if sid in source_ids:
            errors.append(f"duplicate source id: {sid}")
        source_ids.add(sid)

        required = [
            "displayName",
            "author",
            "officialSourceUrl",
            "uploadedArchives",
            "licenseStatus",
            "commercialRuntimePolicy",
            "publicRepoPolicy",
            "rawAssetPolicy",
            "rawQuarantinePath",
            "candidateFamilies",
            "recommendedUse",
            "prohibitedUse",
        ]
        for key in required:
            if source.get(key) in (None, "", []):
                errors.append(f"{sid} missing required {key}")

        raw_path = source.get("rawQuarantinePath", "")
        if not raw_path.startswith("assets/reference_quarantine/third_party/"):
            errors.append(f"{sid} rawQuarantinePath must stay under quarantine root: {raw_path}")
        else:
            required_quarantine_paths.add(raw_path.rstrip("/"))
            qdir = ROOT / raw_path
            if not qdir.exists():
                errors.append(f"{sid} quarantine directory missing: {raw_path}")

        status = source.get("licenseStatus", "")
        policy = source.get("commercialRuntimePolicy", "")
        repo_policy = source.get("publicRepoPolicy", "")
        raw_policy = source.get("rawAssetPolicy", "")
        processed = source.get("processedPrototypePath")

        if "non_commercial" in status and "blocked" not in policy:
            errors.append(f"{sid} is non-commercial but commercialRuntimePolicy is not blocked")
        if "blocked" in status and "blocked" not in policy:
            errors.append(f"{sid} is blocked but commercialRuntimePolicy is not blocked")
        if "blocked" in policy:
            blocked_ids.add(sid)
            if processed:
                errors.append(f"{sid} blocked source must not have processedPrototypePath: {processed}")
        if "allowed" in policy:
            allowed_ids.add(sid)
            if not processed:
                warnings.append(f"{sid} allowed source has no processedPrototypePath")
        if "raw" not in repo_policy and "do_not_commit" not in repo_policy and "user_supplied" not in repo_policy:
            warnings.append(f"{sid} publicRepoPolicy may be too vague: {repo_policy}")
        if raw_policy not in {"quarantine_or_user_supplied_raw", "reference_quarantine_only"}:
            errors.append(f"{sid} unsupported rawAssetPolicy: {raw_policy}")

    queue_ids: set[str] = set()
    for entry in queue_entries:
        eid = entry.get("id")
        if not eid:
            errors.append("queue entry missing id")
            continue
        if eid in queue_ids:
            errors.append(f"duplicate queue entry id: {eid}")
        queue_ids.add(eid)
        source_id = entry.get("externalSourceId")
        if source_id not in source_ids:
            errors.append(f"{eid} references missing externalSourceId {source_id}")
        status = entry.get("status", "")
        outputs = entry.get("targetOutputs") or []
        if "blocked" in status and outputs:
            errors.append(f"{eid} blocked queue entry must not define targetOutputs")
        if source_id in blocked_ids and outputs:
            errors.append(f"{eid} references blocked source {source_id} but declares outputs")
        for output in outputs:
            if not (output.startswith("assets/processed/") or output.startswith("content/assets/")):
                errors.append(f"{eid} target output outside processed asset area: {output}")
            if output.lower().endswith((".png", ".gif")) and "blocked" in status:
                errors.append(f"{eid} blocked entry cannot define image output: {output}")

    if not allowed_ids:
        errors.append("no allowed prototype/runtime candidates registered")
    if len(blocked_ids) < 3:
        warnings.append("expected multiple blocked/reference-only records from audits")

    raw_archive_names = {
        "Asset Pack.zip",
        "Pipoya RPG Tileset 32x32.zip",
        "Door_Animation.zip",
        "Unorganized Parts.zip",
        "free version.zip",
        "Interior free.zip",
        "town free.zip",
        "19.07a - Gentle Forest 3.0a ($0 palettes).zip",
        "FREE Mana Seed Character Base Demo 2.0.zip",
        "sample map and Tiled files.zip",
    }
    # The repository should not contain copied raw source archives under assets/content.
    for root in [ROOT / "assets", ROOT / "content"]:
        if not root.exists():
            continue
        for path in root.rglob("*.zip"):
            if path.name in raw_archive_names:
                errors.append(f"raw uploaded third-party archive copied into repo tree: {rel(path)}")

    # Quarantine folders should be placeholders only in this pass; no raw assets copied yet.
    for raw_path in sorted(required_quarantine_paths):
        qdir = ROOT / raw_path
        if not qdir.exists():
            continue
        payload_files = [p for p in qdir.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if payload_files:
            warnings.append(
                f"{raw_path} contains payload files; verify they are intentionally local/quarantined and not public runtime assets"
            )

    if errors:
        print("Validate-ExternalAssetIntakeV25: FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print("Validate-ExternalAssetIntakeV25: OK")
    print(f"sources={len(sources)} allowed_candidates={len(allowed_ids)} blocked_or_reference={len(blocked_ids)} queue_entries={len(queue_entries)}")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
