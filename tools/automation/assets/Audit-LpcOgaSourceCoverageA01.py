#!/usr/bin/env python3
"""Read-only, offline reconciliation of Havenwild's LPC/OGA discovery and local mounts.

This is a coverage *audit*, not an importer, downloader, rasterizer or promotion path.
Only writes its chosen artifacts/audits report directory. The original catalogs,
third-party artwork, publication records, and PCC state are never mutated.
"""
from __future__ import annotations

import argparse
import csv
import datetime as datetime
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

DISCOVERY = "content/assets/lpc/lpc_ecosystem_discovery_seed_r18_v1.json"
OGA = "content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json"
QUEUE = "content/assets/oga_lpc/manifests/oga_lpc_audit_queue_v0_1.json"
BROWSER = "content/editor/assets/lpc_world_source_browser_v1.json"
OGA_MOUNT = "assets/source/licensed/oga_lpc_prototypes"
EXCLUDED_LPC_PREFIX = "assets/source/licensed/lpc_revised/"
SCHEMA = "havenwild.lpc_oga_source_coverage_a01.v1"


def read_json(root: Path, relative: str) -> dict:
    path = root / relative
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError(f"expected JSON object: {relative}")
    return result


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a source path without confusing the *declared* LPC mount with a leak.

    Raw licensed LPC art may live behind a Windows junction or a directory
    symlink. The catalog explicitly names ``assets/source/licensed/lpc_revised``
    as its mount. That subtree is permitted to resolve outside the checkout,
    but a nested link must still stay within the resolved mount. No other
    external locations are authorized by this read-only audit.
    """
    text = relative.replace("\\", "/")
    path = Path(text)
    if not text or path.is_absolute() or ":" in text or any(p in {"", ".", ".."} for p in text.split("/")):
        raise ValueError(f"unsafe local source path: {relative!r}")
    root_real = root.resolve()
    resolved = (root / path).resolve()
    if resolved.is_relative_to(root_real):
        return resolved

    # Only the exact, pre-existing LPC source-mount subtree is eligible for
    # read-only external resolution. Check the physical target against the
    # resolved mount itself, NOT merely against the repository root. This
    # rejects traversal through another symlink inside the LPC mount.
    lpc_relative = Path(EXCLUDED_LPC_PREFIX.rstrip("/"))
    if path == lpc_relative or lpc_relative in path.parents:
        lpc_mount = root / lpc_relative
        if lpc_mount.is_dir() and resolved.is_relative_to(lpc_mount.resolve()):
            return resolved
    raise ValueError(f"source escapes repository or authorized LPC mount: {relative!r}")


def url_key(url: str | None) -> str:
    """Exact URL identity only. No fuzzy guesses or page equivalence assumptions."""
    if not url:
        return ""
    u = urlparse(url)
    host = u.netloc.lower().removeprefix("www.")
    return f"{host}{u.path.rstrip('/').lower()}" if u.scheme in {"https", "http"} else ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Read PNG IHDR without decoding pixels or relying on an image dependency."""
    with path.open("rb") as stream:
        head = stream.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def audit(root: Path, out: Path, *, hash_sources: bool = False) -> dict:
    discovery = read_json(root, DISCOVERY)
    registry = read_json(root, OGA)
    queue = read_json(root, QUEUE)
    browser = read_json(root, BROWSER)
    packs = discovery.get("packs", [])
    sources = registry.get("sources", [])
    cards = browser.get("entries", [])
    approvals = {row.get("id"): row.get("state", "unknown") for row in queue.get("queue", [])}
    by_page: dict[str, list[str]] = defaultdict(list)
    for entry in sources:
        key = url_key(entry.get("sourcePage"))
        if key:
            by_page[key].append(entry["id"])
    discovered = []
    for pack in packs:
        linked = by_page.get(url_key(pack.get("url")), [])
        discovered.append({
            "discoveryId": pack["id"], "title": pack.get("title", ""),
            "domain": pack.get("domain", ""), "sourcePage": pack.get("url", ""),
            "license": pack.get("selectedLicense") or "UNVERIFIED",
            "discoveryTier": pack.get("tier", "review"),
            "matchedAcquisitionIds": ";".join(sorted(linked)),
            "routeStatus": "exact_page_match" if linked else "discovery_only_no_exact_acquisition_route",
            "action": "inspect_acquisition_record" if linked else "review_exact_source_license_and_add_approved_route",
        })
    oga_rows = []
    mount = root / OGA_MOUNT
    for entry in sources:
        sid = entry["id"]
        local = ""
        original_sha = ""
        expected_sha = ""
        error = ""
        license_value = entry.get("selectedLicense") or "UNVERIFIED"
        route = entry.get("acquisition", "direct_url" if entry.get("directUrl") else "no_download_route")
        images_present = None
        archive_state = "not_applicable"
        if route == "reference_only":
            state = "reference_only"
        elif route == "existing_pinned_elizawy_repository":
            local = entry.get("localSourceRoot", "")
            try:
                state = "mounted_provider" if safe_path(root, local).is_dir() else "provider_absent_in_this_checkout"
            except ValueError as exc:
                state, error = "invalid_local_path", str(exc)
        elif entry.get("fileName") and entry.get("directUrl"):
            base = f"{OGA_MOUNT}/{sid.replace('.', '_')}"
            local = f"{base}/source/{entry['fileName']}"
            try:
                archive = safe_path(root, local)
                extracted = safe_path(root, f"{base}/extracted")
                record_path = safe_path(root, f"{base}/source_record.json")
                if not archive.is_file():
                    state = "archive_absent_in_this_checkout"
                    archive_state = "absent"
                else:
                    archive_state = "present"
                    if hash_sources:
                        original_sha = sha256_file(archive)
                    if record_path.is_file():
                        record = json.loads(record_path.read_text(encoding="utf-8-sig"))
                        expected_sha = str(record.get("sha256") or "")
                        if expected_sha and not original_sha:
                            original_sha = sha256_file(archive)
                    # Do not recurse into vast raw provider trees. A single extracted
                    # file confirms extraction exists; contents need a separate audit.
                    has_extracted_files = extracted.is_dir() and any(extracted.iterdir())
                    state = "archive_and_extraction_present" if has_extracted_files else "archive_only_needs_extraction"
                    if expected_sha and expected_sha.lower() != original_sha.lower():
                        state, error = "sha256_mismatch", "source_record_sha256_does_not_match_archive"
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                state, error = "local_source_check_failed", str(exc)
        else:
            state = "no_download_route"
        oga_rows.append({
            "sourceId": sid, "title": entry.get("title", ""), "sourcePage": entry.get("sourcePage", ""),
            "selectedLicense": license_value, "licenseState": "declared_review_required" if license_value == "UNVERIFIED" else "declared_not_reverified",
            "priority": entry.get("prototypePriority", ""), "approvalState": approvals.get(sid, "not_in_audit_queue"),
            "route": route, "localPath": local, "mountState": state,
            "archiveState": archive_state, "sha256": original_sha, "expectedSha256": expected_sha,
            "sourceImagesVerified": images_present, "editorExposure": "not_in_lpc_revised_sheet_browser_by_default",
            "runtimeCertified": "NOT_ESTABLISHED", "error": error,
        })
    lpc_rows = []
    lpc_mount = root / EXCLUDED_LPC_PREFIX
    for card in cards:
        source = card.get("sourcePath", "")
        dims = card.get("imageSize", [])
        actual = None
        digest = ""
        error = ""
        try:
            file = safe_path(root, source)
            if not file.is_file():
                state = "source_absent_in_this_checkout"
            else:
                actual = png_dimensions(file) if file.suffix.lower() == ".png" else None
                state = "source_present"
                if actual is None and file.suffix.lower() == ".png":
                    state = "invalid_png_header"
                elif actual is not None and list(actual) != dims:
                    state = "image_dimensions_mismatch"
                if hash_sources:
                    digest = sha256_file(file)
        except (ValueError, OSError) as exc:
            state, error = "source_check_failed", str(exc)
        lpc_rows.append({
            "stableId": card.get("stableId", ""), "label": card.get("displayName", ""),
            "category": card.get("category", ""), "sourcePath": source,
            "expectedSize": "x".join(map(str, dims)), "actualSize": "x".join(map(str, actual)) if actual else "",
            "sliceSize": "x".join(map(str, card.get("sliceSize", []))),
            "productionState": card.get("productionState", "unknown"),
            "mountState": state, "sha256": digest,
            "requiresLicensedSourceMount": source.startswith(EXCLUDED_LPC_PREFIX),
            "runtimeCertified": "NOT_ESTABLISHED", "error": error,
        })
    # Make conflicts visible; don't silently pick one ID, source, or license.
    ids = Counter(r["stableId"] for r in lpc_rows)
    paths = Counter(r["sourcePath"].casefold() for r in lpc_rows)
    oga_ids = Counter(r["sourceId"] for r in oga_rows)
    issues = []
    for name, count in sorted(ids.items()):
        if count > 1: issues.append({"kind": "duplicate_lpc_stable_id", "id": name, "count": count})
    for name, count in sorted(paths.items()):
        if count > 1: issues.append({"kind": "duplicate_lpc_source_path", "id": name, "count": count})
    for name, count in sorted(oga_ids.items()):
        if count > 1: issues.append({"kind": "duplicate_oga_source_id", "id": name, "count": count})
    if len(cards) != browser.get("entryCount"):
        issues.append({"kind": "browser_entry_count_mismatch", "id": BROWSER, "count": len(cards)})
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "discovery_coverage.csv", discovered, ["discoveryId", "title", "domain", "sourcePage", "license", "discoveryTier", "matchedAcquisitionIds", "routeStatus", "action"])
    write_csv(out / "oga_source_mounts.csv", oga_rows, ["sourceId", "title", "sourcePage", "selectedLicense", "licenseState", "priority", "approvalState", "route", "localPath", "mountState", "archiveState", "sha256", "expectedSha256", "sourceImagesVerified", "editorExposure", "runtimeCertified", "error"])
    write_csv(out / "lpc_browser_sheet_mounts.csv", lpc_rows, ["stableId", "label", "category", "sourcePath", "expectedSize", "actualSize", "sliceSize", "productionState", "mountState", "sha256", "requiresLicensedSourceMount", "runtimeCertified", "error"])
    write_csv(out / "conflicts.csv", issues, ["kind", "id", "count"])
    summary = {
        "schema": SCHEMA, "generatedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checkoutRoot": str(root), "scope": "this_checkout_only",
        "authorities": {"discovery": DISCOVERY, "acquisitionRegistry": OGA, "approvalQueue": QUEUE, "lpcBrowser": BROWSER},
        "counts": {"discoveredPacks": len(discovered), "curatedOgaRecords": len(oga_rows),
                   "approvalQueueEntries": len(queue.get("queue", [])), "lpcBrowserCards": len(lpc_rows),
                   "discoveryExactPageMatches": sum(bool(r["matchedAcquisitionIds"]) for r in discovered),
                   "discoveryWithoutExactRoute": sum(not r["matchedAcquisitionIds"] for r in discovered)},
        "ogaMountStates": dict(sorted(Counter(r["mountState"] for r in oga_rows).items())),
        "lpcMountStates": dict(sorted(Counter(r["mountState"] for r in lpc_rows).items())),
        "lpcProductionStates": dict(sorted(Counter(r["productionState"] for r in lpc_rows).items())),
        "lpcMountRootPresent": lpc_mount.is_dir(), "ogaMountRootPresent": mount.is_dir(),
        "conflicts": issues,
        "interpretation": [
            "A source absent in THIS checkout is not necessarily absent on the developer's Windows machine; lean rollups deliberately exclude raw licensed LPC mounts.",
            "Exact source page equality links discovery and acquisition records; unmatched records remain visible, never silently deduplicated.",
            "A listed license is a declared choice, not a re-verified legal or source-file provenance check.",
            "Mounted files do not imply correct slices, reviewed semantics, runtime certification, or editor exposure.",
            "The LPC Revised world browser excludes other OGA prototype sources by construction.",
            "No downloads, promotions, repo-source writes, or world/scene mutations were performed.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = ["# Havenwild A01 — LPC/OGA source reconciliation", "", f"Checkout: `{root}`", "",
             f"- Discovery packs: **{len(discovered)}**; exact-page acquisition matches: **{summary['counts']['discoveryExactPageMatches']}**; unlinked discovery records: **{summary['counts']['discoveryWithoutExactRoute']}**.",
             f"- Curated acquisition sources: **{len(oga_rows)}**; queue records: **{len(queue.get('queue', []))}**.",
             f"- LPC Revised browser sheets: **{len(lpc_rows)}**; browser source mount present: **{lpc_mount.is_dir()}**.",
             f"- OGA prototype source mount present: **{mount.is_dir()}**.",
             "", "## OGA mount states", ""]
    lines.extend(f"- `{k}`: {v}" for k, v in summary["ogaMountStates"].items())
    lines += ["", "## LPC sheet states", ""]
    lines.extend(f"- `{k}`: {v}" for k, v in summary["lpcMountStates"].items())
    lines += ["", "## What to do next", "",
              "1. Run this exact audit in the *live hydrated Windows repository* before declaring images missing. Do not replace source folders from a lean rollup.",
              "2. Review discovery_coverage.csv for unlinked source pages and unresolved exact licenses; approve routes individually, no automatic bulk downloads.",
              "3. Review oga_source_mounts.csv for missing archives or extractions, sha mismatches and absent source records.",
              "4. Review lpc_browser_sheet_mounts.csv for missing mounts, broken PNGs and image-size mismatches; do not assume grid slices are correct merely because dimensions match.",
              "5. Only after source coverage is known, reconcile mapping/assembly/runtime consumers and add editor browsing for approved OGA sources.",
              "", "**This report is not runtime, visual, licensing or gameplay certification.**", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline, read-only Havenwild LPC/OGA source reconciliation")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, default=None, help="Report directory; defaults to timestamped artifacts/audits/lpc-oga-source-coverage")
    parser.add_argument("--hash-sources", action="store_true", help="Compute SHA-256 of all mounted LPC browser PNGs and OGA archives (slower)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    out = args.output.resolve() if args.output else root / "artifacts/audits/lpc-oga-source-coverage" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    summary = audit(root, out, hash_sources=args.hash_sources)
    print(f"A01 source reconciliation: {out}")
    print("Counts:", summary["counts"])
    print("OGA mounts:", summary["ogaMountStates"])
    print("LPC sheets:", summary["lpcMountStates"])
    print("Source files unchanged; no downloads or asset promotion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
