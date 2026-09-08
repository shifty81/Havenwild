#!/usr/bin/env python3
"""Shared Havenwild normal-source-rollup policy reader.

This module intentionally decides *what belongs in a normal reproducible source
handoff*, not what belongs in incremental patches or offline recovery bundles.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Iterable

POLICY_RELATIVE = Path("content/architecture/havenwild_source_rollup_policy_v1.json")
MACHINE_LOCAL_ROOTS = {
    ".git",
    ".havenwild",
    ".local",
    ".logs",
    "artifacts",
    "Build",
    "IMPORTS",
    "logs",
    "target",
}
MACHINE_LOCAL_PREFIXES = (
    "assets/source/licensed/",
    "WORKSPACE/generated/",
    "WORKSPACE/dev_bridge/",
    "WORKSPACE/test-output/",
    "WORKSPACE/saves/",
    "WORKSPACE/recovery/",
    "WORKSPACE/profiles/",
    "node_modules/",
)


def load_policy(root: Path) -> dict:
    path = root / POLICY_RELATIVE
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize(relative: str | Path) -> str:
    return Path(relative).as_posix().lstrip("./")


def _under(relative: str, prefix: str) -> bool:
    clean = prefix.replace("\\", "/").strip("/")
    return relative == clean or relative.startswith(clean + "/")


def excluded_from_normal_rollup(relative: str | Path, policy: dict) -> bool:
    rel = _normalize(relative)
    if not rel:
        return False
    parts = Path(rel).parts
    if parts and parts[0] in MACHINE_LOCAL_ROOTS:
        return True
    if "__pycache__" in parts or "node_modules" in parts:
        return True
    if Path(rel).suffix.lower() in {".pyc", ".pyo"}:
        return True
    if any(_under(rel, prefix) for prefix in MACHINE_LOCAL_PREFIXES):
        return True

    normal = policy["normalRollup"]
    if any(_under(rel, prefix) for prefix in normal.get("alwaysRetainPrefixes", [])):
        return False
    exact = {item.replace("\\", "/").strip("/") for item in normal.get("excludeExactPaths", [])}
    if rel in exact:
        return True
    if any(_under(rel, prefix) for prefix in normal.get("excludePrefixes", [])):
        return True
    name = Path(rel).name
    if any(fnmatch.fnmatch(name, pattern) for pattern in normal.get("excludeNamePatterns", [])):
        return True
    return False


def iter_normal_rollup_files(root: Path, *, output: Path | None = None) -> Iterable[Path]:
    policy = load_policy(root)
    output_resolved = output.resolve() if output is not None else None
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            if path.is_symlink():
                continue
        except OSError:
            continue
        if output_resolved is not None and path.resolve() == output_resolved:
            continue
        relative = path.relative_to(root)
        if not excluded_from_normal_rollup(relative, policy):
            yield path
