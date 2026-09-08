#!/usr/bin/env python3
"""Audit and normalize the complete pinned ElizaWy/LPC repository for Havenwild.

The raw third-party source tree remains intact so source-local credits and
folder context are preserved. This tool builds a virtual, project-owned index
that routes every source file into the correct Havenwild domain. Runtime and
editor systems consume derived catalogs/atlases; they never move or rename the
raw LPC files.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import struct
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/source/licensed/lpc_revised"
AUTHORITY = ROOT / "content/assets/lpc/lpc_project_asset_authority_v0_1.json"
LOCK = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
OUTPUT_ROOT = ROOT / "WORKSPACE/generated/lpc"
AUDIT_GZ = OUTPUT_ROOT / "elizawy_repository_audit_v167z38.json.gz"
SUMMARY = OUTPUT_ROOT / "elizawy_repository_audit_v167z38_summary.json"
CATALOG_ROOT = OUTPUT_ROOT / "catalogs"
REPORT = ROOT / "docs/audits/generated/ELIZAWY_PROJECT_ASSET_AUDIT_V167Z38.md"
REVISION = OUTPUT_ROOT / ".elizawy_repository_audit_revision"
PROJECT_ASSET_CATALOG = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"
REVISION_ID = "167Z38-project-wide-elizawy-authority-v2"
SOURCE_MOUNT_PROVENANCE = OUTPUT_ROOT / "elizawy_source_mount_v167z38.json"

IMAGE_EXTENSIONS = {".png", ".gif", ".jpg", ".jpeg", ".webp"}
TEXT_EXTENSIONS = {".txt", ".md", ".license", ".csv"}
METADATA_EXTENSIONS = {".json", ".xml", ".tsx", ".tmx", ".ron", ".yml", ".yaml"}
AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3"}
EXCLUDED_PARTS = {".git", "__pycache__", "node_modules"}
CREDIT_TOKENS = ("credits", "credit", "license", "licence", "copying", "authors", "attribution")
SEASONS = ("spring", "summer", "autumn", "winter_ice", "winter")

ROLE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("tree", ("tree", "trees", "sapling", "stump", "trunk")),
    ("mushroom", ("mushroom", "fungus")),
    ("flower", ("flower", "wildflower")),
    ("plant", ("plant", "shrub", "bush", "grass", "reed", "herb", "weed")),
    ("rock", ("rock", "boulder", "ore", "mineral")),
    ("water", ("water", "shallows", "waterfall", "foam", "ice")),
    ("cliff", ("cliff", "ledge", "ramp", "mountain")),
    ("farm", ("tilled", "soil", "crop", "seed", "farm")),
    ("bridge", ("bridge",)),
    ("floor", ("floor", "carpet", "rug")),
    ("wall", ("wall",)),
    ("door", ("door", "gate")),
    ("window", ("window",)),
    ("roof", ("roof",)),
    ("fence", ("fence",)),
    ("stairs", ("stairs", "stair", "ladder")),
    ("furniture", ("chair", "table", "bed", "cabinet", "shelf", "counter", "bench")),
    ("storage", ("crate", "barrel", "chest", "storage", "sack")),
    ("lighting", ("lamp", "light", "candle", "torch", "fireplace")),
    ("food", ("food", "fruit", "vegetable", "bread", "meat", "fish", "drink")),
    ("tool", ("tool", "axe", "pickaxe", "hoe", "watering", "fishing", "hammer", "scythe")),
    ("weapon", ("weapon", "sword", "spear", "bow", "shield", "staff", "dagger")),
    ("armor", ("armor", "armour", "helmet")),
    ("clothing", ("clothing", "shirt", "pants", "dress", "skirt", "boots", "shoes", "hat")),
    ("hair", ("hair", "beard", "mustache", "moustache")),
    ("body", ("body", "base", "head", "face", "skin")),
    ("animation", ("animation", "walk", "idle", "slash", "thrust", "shoot", "spell", "hurt", "run")),
    ("effect", ("effect", "fx", "particle", "projectile", "magic", "spark", "smoke")),
    ("palette", ("palette", "ramp", "swatch")),
    ("reference_scene", ("test scene", "test_scene", "preview", "demo")),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_json_gz(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as stream:
        json.dump(payload, stream, separators=(",", ":"), ensure_ascii=False)
        stream.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> list[int] | None:
    try:
        suffix = path.suffix.lower()
        if suffix == ".png":
            with path.open("rb") as stream:
                header = stream.read(24)
            if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
                return list(struct.unpack(">II", header[16:24]))
        # Non-PNG dimensions are left for an editor importer to inspect. PNG is
        # the production format used by the current LPC runtime pipeline.
    except OSError:
        return None
    return None


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", ".", value.lower()).strip(".") or "unnamed"


def stable_asset_id(domain: str, relative: str) -> str:
    """Build a readable ID with a path-derived collision guard.

    LPC contains many repeated names and punctuation/case variants. A short SHA-1
    suffix keeps IDs stable across machines while preventing two unrelated
    source files from collapsing onto one project asset identifier.
    """
    stem = relative.rsplit(".", 1)[0]
    normalized = relative.replace("\\", "/").casefold().encode("utf-8")
    suffix = hashlib.sha1(normalized).hexdigest()[:10]
    return f"lpc.{domain}.{slug(stem)}.{suffix}"


def source_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in TEXT_EXTENSIONS:
        return "documentation"
    if suffix in METADATA_EXTENSIONS:
        return "metadata"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    return "support"


def detect_season(relative: str) -> str | None:
    lowered = relative.lower().replace("-", "_")
    for season in SEASONS:
        if season in lowered:
            return season
    return None


def detect_theme(relative: str) -> str:
    lowered = relative.lower()
    if "modern" in lowered:
        return "modern"
    if "sci-fi" in lowered or "scifi" in lowered or "science fiction" in lowered:
        return "science_fiction"
    if "fantasy" in lowered or relative.startswith(("Terrain/", "Structure/")):
        return "fantasy_or_neutral"
    return "neutral_or_unspecified"


def detect_roles(relative: str) -> list[str]:
    lowered = relative.lower().replace("_", " ").replace("-", " ")
    roles = [role for role, tokens in ROLE_RULES if any(token in lowered for token in tokens)]
    return roles or ["uncategorized_source"]


def route_domain(relative: str, authority: dict[str, Any]) -> str:
    lowered = relative.lower()
    name = Path(relative).name.lower()
    # Nature is a deliberate project domain layered over the Terrain folder.
    if relative.startswith("Terrain/") and any(
        token in name
        for token in (
            "tree", "sapling", "stump", "trunk", "plant", "flower",
            "wildflower", "mushroom", "fungus", "rock", "boulder",
            "ore", "mineral", "shrub", "bush", "reed", "herb",
        )
    ):
        return "nature"
    if any(token in name for token in CREDIT_TOKENS) or relative in {"Credits.txt", "README.md"}:
        return "legal_and_documentation"
    if relative in {"GithubReadme.png", "GithubCharacterDemo.gif", ".gitignore"}:
        return "repository_support"
    for domain in authority["domains"]:
        if domain["id"] in {"nature", "legal_and_documentation"}:
            continue
        if any(relative.startswith(prefix) for prefix in domain.get("sourcePrefixes", [])):
            return domain["id"]
    if lowered.endswith(("readme.md", "credits.txt")):
        return "legal_and_documentation"
    return "unrouted_source_support"


def nearest_credits(path: Path, source_root: Path, cache: dict[Path, list[str]]) -> list[str]:
    parent = path.parent
    if parent in cache:
        return cache[parent]
    found: list[str] = []
    cursor = parent
    while True:
        try:
            candidates = sorted(
                item for item in cursor.iterdir()
                if item.is_file() and any(token in item.name.lower() for token in CREDIT_TOKENS)
            )
        except OSError:
            candidates = []
        for candidate in candidates:
            relative = candidate.relative_to(source_root).as_posix()
            if relative not in found:
                found.append(relative)
        if cursor == source_root:
            break
        if source_root not in cursor.parents:
            break
        cursor = cursor.parent
    root_credit = source_root / "Credits.txt"
    if root_credit.is_file() and "Credits.txt" not in found:
        found.append("Credits.txt")
    cache[parent] = found
    return found


def project_route(domain_id: str, authority: dict[str, Any]) -> dict[str, Any]:
    for domain in authority["domains"]:
        if domain["id"] == domain_id:
            return domain
    return {
        "id": domain_id,
        "catalog": f"WORKSPACE/generated/lpc/catalogs/{domain_id}.json",
        "projectNamespaces": [f"source.{domain_id}"],
        "owners": ["asset_audit"],
        "runtimePolicy": "not_runtime_eligible_without_explicit_route",
    }


def classify_readiness(kind: str, domain: str, credits: list[str], dimensions: list[int] | None) -> str:
    if domain == "reference_scenes":
        return "reference_only"
    if domain == "legal_and_documentation":
        return "indexed_legal"
    if kind == "metadata":
        return "metadata_candidate"
    if kind == "documentation":
        return "indexed_documentation"
    if kind == "audio":
        return "explicit_fx_review_required"
    if kind != "image":
        return "source_support"
    if not credits:
        return "blocked_missing_credit_context"
    if dimensions is None:
        return "manual_import_review_required"
    return "catalogued_requires_semantic_promotion"


def build_record(path: Path, source_root: Path, authority: dict[str, Any], credit_cache: dict[Path, list[str]], do_hash: bool) -> dict[str, Any]:
    relative = path.relative_to(source_root).as_posix()
    domain = route_domain(relative, authority)
    route = project_route(domain, authority)
    kind = source_kind(path)
    dimensions = image_dimensions(path) if kind == "image" else None
    credits = nearest_credits(path, source_root, credit_cache)
    roles = detect_roles(relative)
    record: dict[str, Any] = {
        "sourcePath": relative,
        "sourceKind": kind,
        "primaryDomain": domain,
        "semanticRoles": roles,
        "stableAssetId": stable_asset_id(domain, relative),
        "theme": detect_theme(relative),
        "season": detect_season(relative),
        "dimensions": dimensions,
        "grid": {
            "baseTile": [32, 32],
            "widthAligned": bool(dimensions and dimensions[0] % 32 == 0),
            "heightAligned": bool(dimensions and dimensions[1] % 32 == 0),
        } if dimensions else None,
        "nearestCredits": credits,
        "creditCoverage": "source_local_or_root" if credits else "missing",
        "catalogPath": route.get("catalog"),
        "projectNamespaces": route.get("projectNamespaces", []),
        "systemOwners": route.get("owners", []),
        "runtimePolicy": route.get("runtimePolicy"),
        "readiness": classify_readiness(kind, domain, credits, dimensions),
        "sourceSizeBytes": path.stat().st_size,
    }
    if do_hash:
        record["sha256"] = sha256(path)
    return record


def source_files(source_root: Path) -> list[Path]:
    return sorted(
        path for path in source_root.rglob("*")
        if path.is_file() and not any(part in EXCLUDED_PARTS for part in path.relative_to(source_root).parts)
    )


def build_audit(source_root: Path, authority: dict[str, Any], lock: dict[str, Any], do_hash: bool) -> dict[str, Any]:
    credit_cache: dict[Path, list[str]] = {}
    records: list[dict[str, Any]] = []
    domain_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    readiness_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    missing_credits: list[str] = []
    duplicate_ids: dict[str, list[str]] = defaultdict(list)

    paths = source_files(source_root)
    for index, path in enumerate(paths, start=1):
        record = build_record(path, source_root, authority, credit_cache, do_hash)
        records.append(record)
        domain_counts[record["primaryDomain"]] += 1
        kind_counts[record["sourceKind"]] += 1
        readiness_counts[record["readiness"]] += 1
        for role in record["semanticRoles"]:
            role_counts[role] += 1
        if record["creditCoverage"] == "missing" and record["sourceKind"] == "image":
            missing_credits.append(record["sourcePath"])
        duplicate_ids[record["stableAssetId"]].append(record["sourcePath"])
        if index % 2500 == 0:
            print(f"  audited {index:,}/{len(paths):,} ElizaWy/LPC files", flush=True)

    duplicates = {key: value for key, value in duplicate_ids.items() if len(value) > 1}
    required_top_level = lock.get("requiredTopLevelPaths", [])
    required_root_files = lock.get("requiredRootFiles", [])
    required_terrain = lock.get("requiredTerrainFiles", [])
    missing_top_level = [item for item in required_top_level if not (source_root / item).exists()]
    missing_root_files = [item for item in required_root_files if not (source_root / item).is_file()]
    missing_terrain = [item for item in required_terrain if not (source_root / item).is_file()]
    unrouted = [record["sourcePath"] for record in records if record["primaryDomain"] == "unrouted_source_support"]
    required_domains = {domain["id"] for domain in authority["domains"]}
    missing_domains = sorted(required_domains - set(domain_counts))

    mount_provenance = {}
    if SOURCE_MOUNT_PROVENANCE.is_file():
        try:
            mount_provenance = load_json(SOURCE_MOUNT_PROVENANCE)
        except (OSError, json.JSONDecodeError):
            mount_provenance = {"verificationMode": "invalid_mount_provenance"}
    source_revision_verified = (
        mount_provenance.get("expectedCommit") == authority["source"]["commit"]
        and mount_provenance.get("verified") is True
    )

    return {
        "schema": "havenwild.elizawy_repository_audit.v167z38",
        "revision": REVISION_ID,
        "generatedAtUnixSeconds": int(time.time()),
        "source": {
            "repository": authority["source"]["repository"],
            "commit": authority["source"]["commit"],
            "mount": source_root.relative_to(ROOT).as_posix(),
            "fileCount": len(records),
            "hashed": do_hash,
            "mountProvenance": SOURCE_MOUNT_PROVENANCE.relative_to(ROOT).as_posix(),
            "sourceRevisionVerified": source_revision_verified,
            "verificationMode": mount_provenance.get("verificationMode", "source_structure_and_locked_file"),
        },
        "policy": authority["projectPolicy"],
        "summary": {
            "domainCounts": dict(sorted(domain_counts.items())),
            "kindCounts": dict(sorted(kind_counts.items())),
            "readinessCounts": dict(sorted(readiness_counts.items())),
            "semanticRoleCounts": dict(sorted(role_counts.items())),
            "missingRequiredTopLevelPaths": missing_top_level,
            "missingRequiredRootFiles": missing_root_files,
            "missingRequiredTerrainFiles": missing_terrain,
            "missingRequiredDomains": missing_domains,
            "sourceRevisionVerified": source_revision_verified,
            "unroutedFileCount": len(unrouted),
            "missingImageCreditContextCount": len(missing_credits),
            "duplicateStableAssetIdCount": len(duplicates),
            "coverageComplete": (
                not missing_top_level
                and not missing_root_files
                and not missing_terrain
                and not missing_domains
                and source_revision_verified
                and not unrouted
                and not duplicates
            ),
        },
        "diagnostics": {
            "unroutedFiles": unrouted,
            "imagesWithoutCreditContext": missing_credits,
            "duplicateStableAssetIds": duplicates,
            "missingRequiredRootFiles": missing_root_files,
            "missingRequiredTerrainFiles": missing_terrain,
            "missingRequiredDomains": missing_domains,
        },
        "records": records,
    }


def write_catalogs(audit: dict[str, Any], authority: dict[str, Any]) -> None:
    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    records_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in audit["records"]:
        records_by_domain[record["primaryDomain"]].append(record)

    known_domains = [domain["id"] for domain in authority["domains"]]
    if "unrouted_source_support" in records_by_domain:
        known_domains.append("unrouted_source_support")
    for domain_id in known_domains:
        route = project_route(domain_id, authority)
        records = records_by_domain.get(domain_id, [])
        write_json(
            CATALOG_ROOT / f"{domain_id}.json",
            {
                "schema": "havenwild.elizawy_domain_catalog.v167z38",
                "revision": REVISION_ID,
                "domain": domain_id,
                "sourceCommit": authority["source"]["commit"],
                "projectNamespaces": route.get("projectNamespaces", []),
                "systemOwners": route.get("owners", []),
                "runtimePolicy": route.get("runtimePolicy"),
                "recordCount": len(records),
                "records": records,
            },
        )



def write_project_asset_catalog(authority: dict[str, Any]) -> None:
    indexes = [
        {
            "id": "elizawy_project_authority",
            "kind": "project_asset_authority",
            "path": AUTHORITY.relative_to(ROOT).as_posix(),
            "editorUse": "project_asset_root",
        },
        {
            "id": "elizawy_repository_audit",
            "kind": "source_audit_summary",
            "path": SUMMARY.relative_to(ROOT).as_posix(),
            "editorUse": "source_coverage_status",
        },
    ]
    for domain in authority["domains"]:
        indexes.append(
            {
                "id": f"elizawy_{domain['id']}",
                "kind": "elizawy_domain_catalog",
                "path": f"WORKSPACE/generated/lpc/catalogs/{domain['id']}.json",
                "editorUse": "domain_asset_browser",
            }
        )
    # Preserve known secondary indexes when a prior generated catalog exists.
    secondary: list[dict[str, Any]] = []
    if PROJECT_ASSET_CATALOG.is_file():
        try:
            prior = load_json(PROJECT_ASSET_CATALOG)
            secondary = [
                item for item in prior.get("indexes", [])
                if item.get("id") not in {entry["id"] for entry in indexes}
            ]
        except (OSError, json.JSONDecodeError):
            secondary = []
    write_json(
        PROJECT_ASSET_CATALOG,
        {
            "schema": "havenwild.asset_catalog.v0_1",
            "updatedAtUnixSeconds": int(time.time()),
            "purpose": "Project-wide asset index with ElizaWy/LPC as the primary visual foundation.",
            "primaryAuthority": AUTHORITY.relative_to(ROOT).as_posix(),
            "primarySource": authority["source"]["id"],
            "indexes": [*indexes, *secondary],
            "editorContracts": {
                "rootCollection": "ElizaWy/LPC",
                "runtimeAndEditorShareCatalogs": True,
                "rawSourceTreeRemainsImmutable": True,
                "promotionRequiresSemanticRoleFootprintCollisionAndCreditContext": True,
            },
        },
    )

def write_report(audit: dict[str, Any], authority: dict[str, Any]) -> None:
    summary = audit["summary"]
    lines = [
        "# ElizaWy/LPC Project Asset Audit — Pass 167Z38",
        "",
        f"- Source: `{authority['source']['repository']}`",
        f"- Pinned commit: `{authority['source']['commit']}`",
        f"- Files indexed: **{audit['source']['fileCount']:,}**",
        f"- Coverage complete: **{summary['coverageComplete']}**",
        f"- Unrouted files: **{summary['unroutedFileCount']}**",
        f"- Duplicate stable IDs: **{summary['duplicateStableAssetIdCount']}**",
        f"- Source revision provenance verified: **{summary['sourceRevisionVerified']}**",
        f"- Images without source-local/root credit context: **{summary['missingImageCreditContextCount']}**",
        "",
        "## Domain routing",
        "",
        "| Domain | Files | Project owners |",
        "|---|---:|---|",
    ]
    by_id = {domain["id"]: domain for domain in authority["domains"]}
    for domain_id, count in summary["domainCounts"].items():
        owners = ", ".join(by_id.get(domain_id, {}).get("owners", ["asset_audit"]))
        lines.append(f"| `{domain_id}` | {count:,} | {owners} |")
    lines.extend([
        "",
        "## Source handling",
        "",
        "The mounted ElizaWy/LPC repository remains intact. Havenwild routes assets through derived catalogs and generated atlases so local Credits files, original paths, and source context are never lost.",
        "",
        "## Tree-first world construction",
        "",
        "Temperate biome generation reserves authored infrastructure first, then places natural-scale tree canopies and one-tile trunk collisions, then derives understory, flowers, mushrooms, herbs, reeds, and rocks from tree/water proximity. Generic circle tree fallbacks are prohibited.",
        "",
        "## Generated outputs",
        "",
        f"- Full compressed audit: `{AUDIT_GZ.relative_to(ROOT).as_posix()}`",
        f"- Summary: `{SUMMARY.relative_to(ROOT).as_posix()}`",
        f"- Domain catalogs: `{CATALOG_ROOT.relative_to(ROOT).as_posix()}`",
    ])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def can_skip(source_root: Path, authority: dict[str, Any], force: bool) -> bool:
    if force or not REVISION.is_file() or not SUMMARY.is_file() or not AUDIT_GZ.is_file():
        return False
    if REVISION.read_text(encoding="utf-8").strip() != REVISION_ID:
        return False
    try:
        summary = load_json(SUMMARY)
    except (OSError, json.JSONDecodeError):
        return False
    return (
        summary.get("revision") == REVISION_ID
        and summary.get("sourceCommit") == authority["source"]["commit"]
        and summary.get("sourceRoot") == source_root.relative_to(ROOT).as_posix()
        and summary.get("coverageComplete") is True
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-hash", action="store_true", help="skip per-file SHA-256 for a faster development audit")
    parser.add_argument("--strict", action="store_true", help="fail for unrouted files, duplicate IDs, or missing required source paths")
    args = parser.parse_args()

    source_root = args.source if args.source.is_absolute() else ROOT / args.source
    authority = load_json(AUTHORITY)
    lock = load_json(LOCK)
    if not source_root.is_dir():
        raise SystemExit(f"ElizaWy/LPC source mount is missing: {source_root}")

    if can_skip(source_root, authority, args.force):
        print(f"ElizaWy/LPC project audit already current: {SUMMARY.relative_to(ROOT)}")
        return 0

    print(f"Auditing complete ElizaWy/LPC source tree: {source_root}")
    audit = build_audit(source_root, authority, lock, do_hash=not args.no_hash)
    write_json_gz(AUDIT_GZ, audit)
    write_catalogs(audit, authority)
    write_project_asset_catalog(authority)
    write_report(audit, authority)

    summary_payload = {
        "schema": "havenwild.elizawy_repository_audit_summary.v167z38",
        "revision": REVISION_ID,
        "sourceCommit": authority["source"]["commit"],
        "sourceRoot": source_root.relative_to(ROOT).as_posix(),
        "fileCount": audit["source"]["fileCount"],
        "verificationMode": audit["source"].get("verificationMode"),
        **audit["summary"],
        "fullAudit": AUDIT_GZ.relative_to(ROOT).as_posix(),
        "catalogRoot": CATALOG_ROOT.relative_to(ROOT).as_posix(),
        "report": REPORT.relative_to(ROOT).as_posix(),
    }
    write_json(SUMMARY, summary_payload)
    REVISION.parent.mkdir(parents=True, exist_ok=True)
    REVISION.write_text(REVISION_ID + "\n", encoding="utf-8")

    print(
        "ElizaWy/LPC audit complete: "
        f"{summary_payload['fileCount']:,} files, "
        f"{len(summary_payload['domainCounts'])} domains, "
        f"coverageComplete={summary_payload['coverageComplete']}"
    )
    if args.strict and not summary_payload["coverageComplete"]:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
