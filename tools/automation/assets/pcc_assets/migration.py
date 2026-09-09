from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RULES = [
    ("intake", ("acquire", "download", "fetch", "prepare-external", "source", "sync")),
    ("catalog", ("catalog", "index", "inventory", "truth", "utilization")),
    ("provenance", ("credit", "license", "attribution", "provenance")),
    ("analyze", ("audit", "analy", "inspect", "detect", "evidence", "review")),
    ("derive", ("atlas", "bake", "generate", "repack", "compose")),
    ("promote", ("promote", "publish", "runtime-cache", "runtimecache")),
    ("certify", ("certif", "acceptance", "authority")),
    ("validate", ("validate", "check", "verify")),
    ("prefab", ("prefab", "building", "structure", "roof", "wall")),
    ("character", ("character", "wardrobe", "player", "ulpc")),
    ("terrain", ("terrain", "cliff", "worldgen", "tile")),
    ("audio", ("audio", "sound", "music")),
]


def classify_tool(path: Path) -> tuple[str, list[str]]:
    name = path.stem.lower()
    matches = []
    for domain, tokens in RULES:
        if any(token in name for token in tokens):
            matches.append(domain)
    if not matches:
        matches = ["review"]
    return matches[0], matches


def inventory_existing_tools(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    automation = repo_root / "tools/automation"
    records = []
    counts = Counter()

    if not automation.is_dir():
        raise FileNotFoundError(f"missing automation root: {automation}")

    for path in sorted(p for p in automation.rglob("*") if p.is_file()):
        if "pcc_assets" in path.parts:
            continue
        if path.name in {"Run-PccAssetTool.cmd", "Run-PccAssetSelfTest.cmd"}:
            continue
        if path.suffix.lower() not in {".py", ".ps1", ".cmd", ".json"}:
            continue

        rel = path.relative_to(repo_root).as_posix()
        primary, matches = classify_tool(path)
        counts[primary] += 1
        records.append({
            "path": rel,
            "extension": path.suffix.lower(),
            "currentDomain": (
                path.relative_to(automation).parts[0]
                if len(path.relative_to(automation).parts) > 1
                else "automation"
            ),
            "normalizationTarget": primary,
            "allMatches": matches,
            "recommendedAction": (
                "extract_reusable_logic_then_wrapper"
                if path.suffix.lower() in {".py", ".ps1"}
                else "retain_as_launcher_or_review"
            ),
            "status": "legacy_or_existing_authority",
        })

    return {
        "schema": "pcc.asset.legacy_tool_inventory.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "repoRoot": repo_root.as_posix(),
        "policy": {
            "deleteExistingToolsAutomatically": False,
            "migrationMethod": "extract -> parity -> wrapper -> PCC command -> archive",
        },
        "summary": {
            "toolCount": len(records),
            "byNormalizationTarget": dict(sorted(counts.items())),
        },
        "tools": records,
    }
