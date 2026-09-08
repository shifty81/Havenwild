#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "WORKSPACE" / "generated" / "asset-catalog.json"
INCLUDED_ROOTS = [
    "assets",
    "content",
    "crates",
    "docs/design",
    "docs/engineering",
    "tools/automation",
    "README.md",
    "Cargo.toml",
    "tools/build/Build.ps1",
    "tools/build/Build.sh",
]
EXCLUDED_SEGMENTS = (
    "/target/",
    "/WORKSPACE/temp/",
    "/crates/crates/",
    "/.git/",
    "/node_modules/",
)


def normalize_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_include(path: Path) -> bool:
    relative = f"/{normalize_relative(path)}/" if path.is_dir() else f"/{normalize_relative(path)}"
    return not any(segment in relative for segment in EXCLUDED_SEGMENTS)


def iter_included_files() -> list[Path]:
    files: list[Path] = []
    for entry in INCLUDED_ROOTS:
        path = ROOT / entry
        if not path.exists():
            continue
        if path.is_dir():
            for child in sorted(p for p in path.rglob("*") if p.is_file()):
                if should_include(child):
                    files.append(child)
        elif should_include(path):
            files.append(path)
    return sorted(files, key=normalize_relative)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(lines: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update("\n".join(lines).encode("utf-8"))
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "name": path.name,
        "path": normalize_relative(path),
        "extension": path.suffix.lstrip(".").lower(),
        "length": stat.st_size,
        "sha256": sha256_file(path),
        "lastWriteTime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def hash_group(files: list[Path]) -> str:
    lines = []
    for path in files:
        stat = path.stat()
        lines.append(f"{normalize_relative(path)} {sha256_file(path)} {stat.st_size}")
    return sha256_text(lines)


def build_catalog() -> dict[str, object]:
    files = iter_included_files()
    records = [file_record(path) for path in files]

    asset_files = [path for path in files if normalize_relative(path).startswith("assets/")]
    content_files = [path for path in files if normalize_relative(path).startswith("content/")]
    source_files = [
        path
        for path in files
        if normalize_relative(path).startswith("crates/") or normalize_relative(path) == "Cargo.toml"
    ]

    return {
        "appInfo": "Havenwild",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "workspaceRoot": str(ROOT),
        "hashes": {
            "sourceTree": hash_group(source_files),
            "generatedAssets": hash_group(asset_files),
            "contentData": hash_group(content_files),
            "assemblyCSharp": hash_group(source_files),
            "resourcesAssets": hash_group(asset_files),
        },
        "files": records,
    }


def main() -> None:
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog()
    DEFAULT_OUTPUT.write_text(f"{json.dumps(catalog, indent=2)}\n", encoding="utf-8")
    print(f"Wrote asset catalog: {DEFAULT_OUTPUT}")
    print(f"Catalog entries: {len(catalog['files'])}")


if __name__ == "__main__":
    main()
