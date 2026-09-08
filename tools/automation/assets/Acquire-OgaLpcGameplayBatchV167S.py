#!/usr/bin/env python3
"""Acquire/audit the curated OpenGameArt LPC prototype dependency lane.

Pass167Z109M restores and expands the historical V167S intake helper. Raw files
remain external authoring dependencies under assets/source/licensed and are
excluded from Havenwild source packages. Downloading never promotes an asset
into runtime content; provider-role, footprint, license and credits validation
still apply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json"
MOUNT = ROOT / "assets/source/licensed/oga_lpc_prototypes"
REPORT = ROOT / "WORKSPACE/generated/oga_lpc_prototypes/sync_report_v0_1.json"
USER_AGENT_PREFIX = "Havenwild-OGA-LPC-Prototype-Intake"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(zf: zipfile.ZipFile, target: Path) -> None:
    target_resolved = target.resolve()
    for member in zf.infolist():
        destination = (target / member.filename).resolve()
        try:
            destination.relative_to(target_resolved)
        except ValueError as exc:
            raise RuntimeError(f"unsafe ZIP member path: {member.filename}") from exc
    zf.extractall(target)


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT_PREFIX})
    temp = path.with_suffix(path.suffix + ".part")
    temp.unlink(missing_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=90) as source, temp.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def source_dir(source_id: str) -> Path:
    return MOUNT / source_id.replace(".", "_")


def discover_credit_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    names = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        lower = path.name.lower()
        if "credit" in lower or "attribution" in lower or lower.startswith("license") or lower.startswith("readme"):
            names.append(path.relative_to(root).as_posix())
    return sorted(names)


def acquire(entry: dict, force: bool, audit_only: bool, registry_revision: str) -> dict:
    result = {
        "id": entry["id"],
        "title": entry["title"],
        "license": entry["selectedLicense"],
        "sourcePage": entry["sourcePage"],
        "status": "pending",
    }

    if entry.get("acquisition") == "reference_only":
        result.update({"status": "reference_only", "localRoot": None})
        return result

    if entry.get("acquisition") == "existing_pinned_elizawy_repository":
        existing = ROOT / entry["localSourceRoot"]
        result.update({
            "status": "existing_provider_ready" if existing.is_dir() else "existing_provider_missing",
            "localRoot": entry["localSourceRoot"],
        })
        return result

    url = entry.get("directUrl")
    filename = entry.get("fileName")
    if not url or not filename:
        result["status"] = "no_download_route"
        return result

    root = source_dir(entry["id"])
    archive = root / "source" / filename
    extracted = root / "extracted"
    record_path = root / "source_record.json"

    if not audit_only and (force or not archive.is_file()):
        download(url, archive)

    if not archive.is_file():
        result["status"] = "missing"
        return result

    digest = sha256(archive)
    if not audit_only:
        if zipfile.is_zipfile(archive):
            if force and extracted.exists():
                shutil.rmtree(extracted)
            if force or not extracted.exists():
                extracted.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(archive) as zf:
                    safe_extract(zf, extracted)
        else:
            extracted.mkdir(parents=True, exist_ok=True)
            copy_target = extracted / filename
            if force or not copy_target.exists():
                shutil.copy2(archive, copy_target)

        source_record = {
            "schema": "havenwild.oga_lpc_local_source_record.v0_1",
            "registryRevision": registry_revision,
            "id": entry["id"],
            "title": entry["title"],
            "sourcePage": entry["sourcePage"],
            "downloadUrl": url,
            "selectedLicense": entry["selectedLicense"],
            "authors": entry.get("authors", []),
            "shareAlike": bool(entry.get("shareAlike", False)),
            "archiveFile": archive.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "roles": entry.get("roles", []),
            "runtimePromoted": False,
            "creditFiles": discover_credit_files(extracted),
        }
        record_path.write_text(json.dumps(source_record, indent=2) + "\n", encoding="utf-8")

    result.update({
        "status": "ready",
        "localRoot": root.relative_to(ROOT).as_posix(),
        "sourceFile": archive.relative_to(ROOT).as_posix(),
        "sha256": digest,
        "creditFiles": discover_credit_files(extracted),
    })
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Acquire every downloadable approved prototype source.")
    parser.add_argument("--priority", type=int, default=None, help="Acquire sources at or above this priority cutoff (1 is highest).")
    parser.add_argument("--id", action="append", dest="ids", default=[], help="Acquire a specific source id; may be repeated.")
    parser.add_argument("--force", action="store_true", help="Redownload/re-extract selected sources.")
    parser.add_argument("--audit-only", action="store_true", help="Do not use network; validate currently mounted files.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero if any selected source fails.")
    parser.add_argument("--best-effort", action="store_true", help="Explicitly continue after optional source failures (default behavior unless --strict).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = data["sources"]

    if args.ids:
        wanted = set(args.ids)
        selected = [entry for entry in entries if entry["id"] in wanted]
        unknown = sorted(wanted - {entry["id"] for entry in selected})
        if unknown:
            print("ERROR unknown source id(s): " + ", ".join(unknown), file=sys.stderr)
            return 2
    elif args.all:
        selected = entries
    elif args.priority is not None:
        selected = [entry for entry in entries if int(entry.get("prototypePriority", 99)) <= args.priority]
    else:
        # Default to the low-friction structural/cave/farm foundation.
        selected = [entry for entry in entries if int(entry.get("prototypePriority", 99)) <= 1]

    results = []
    failures = []
    for entry in selected:
        try:
            result = acquire(entry, force=args.force, audit_only=args.audit_only, registry_revision=str(data.get("revision", "unknown")))
            results.append(result)
            print(f"{result['status'].upper():>24}  {entry['id']}")
            if result["status"] not in {"ready", "existing_provider_ready", "reference_only"}:
                failures.append(result)
        except (OSError, RuntimeError, urllib.error.URLError, zipfile.BadZipFile) as exc:
            result = {"id": entry["id"], "title": entry["title"], "status": "failed", "error": str(exc)}
            results.append(result)
            failures.append(result)
            print(f"FAILED {entry['id']}: {exc}", file=sys.stderr)
            if args.strict:
                break

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "schema": "havenwild.oga_lpc_prototype_sync_report.v0_1",
        "registryRevision": data.get("revision"),
        "selectedCount": len(selected),
        "readyCount": sum(r.get("status") in {"ready", "existing_provider_ready", "reference_only"} for r in results),
        "failureCount": len(failures),
        "results": results,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {REPORT.relative_to(ROOT)}")

    if failures and args.strict:
        return 1
    if failures:
        print(f"WARNING {len(failures)} optional OGA/LPC prototype source(s) are not ready; primary Havenwild/LPC providers remain usable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
