#!/usr/bin/env python3
"""Build the exact Universal LPC CC-BY-SA usage manifest from saved recipes and composite caches."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "WORKSPACE/generated/universal_lpc_character_authority_v167w.json"
OUTPUT = ROOT / "WORKSPACE/generated/universal_lpc_usage_manifest.json"
DEFAULT_SCAN_ROOTS = [
    ROOT / "WORKSPACE/characters",
    ROOT / "WORKSPACE/saves",
    ROOT / "WORKSPACE/cache/lpc_character_composites",
    ROOT / "content/characters/authored",
]

SOURCE_KEYS = {
    "source",
    "source_path",
    "sourcePath",
    "sprite_source",
    "spriteSource",
    "component_source",
    "componentSource",
}
DEPENDENCY_KEYS = {
    "source_dependencies",
    "sourceDependencies",
    "license_dependencies",
    "licenseDependencies",
    "asset_license_dependencies",
}
COMPOSITE_PATH_KEYS = {"composite_path", "compositePath", "cache_path", "cachePath", "output_path", "outputPath"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_source(value: str) -> str:
    value = value.replace("\\", "/").strip()
    marker = "spritesheets/"
    if marker in value:
        value = value.split(marker, 1)[1]
    return value.lstrip("./")


def collect_strings(node: Any, *, key: str | None = None) -> list[tuple[str | None, str]]:
    found: list[tuple[str | None, str]] = []
    if isinstance(node, dict):
        for child_key, value in node.items():
            found.extend(collect_strings(value, key=str(child_key)))
    elif isinstance(node, list):
        for value in node:
            found.extend(collect_strings(value, key=key))
    elif isinstance(node, str):
        found.append((key, node))
    return found


def scan_document(path: Path, conditional_sources: set[str]) -> tuple[set[str], dict[str, set[str]]]:
    data = load_json(path)
    found: set[str] = set()
    dependencies: set[str] = set()
    composite_paths: set[str] = set()

    for key, value in collect_strings(data):
        candidate = normalized_source(value)
        if candidate in conditional_sources:
            found.add(candidate)
            if key in DEPENDENCY_KEYS or key in SOURCE_KEYS:
                dependencies.add(candidate)
        if key in COMPOSITE_PATH_KEYS and value.lower().endswith(".png"):
            composite_paths.add(value.replace("\\", "/"))

    composites: dict[str, set[str]] = {}
    if dependencies:
        for composite in composite_paths:
            composites.setdefault(composite, set()).update(dependencies)
    return found, composites


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, default=AUTHORITY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--scan-root", action="append", type=Path, default=[])
    args = parser.parse_args()

    if not args.authority.is_file():
        raise SystemExit(
            f"Missing {args.authority}. Run tools/automation/characters/Bootstrap-UniversalLpcGenerator.cmd first."
        )
    authority = load_json(args.authority)
    records = authority.get("records", [])
    conditional = {
        record["source"]
        for record in records
        if record.get("license_tier") == "conditional"
        and record.get("share_alike_required") is True
    }

    roots = [path if path.is_absolute() else ROOT / path for path in args.scan_root]
    if not roots:
        roots = DEFAULT_SCAN_ROOTS

    used: set[str] = set()
    composite_dependencies: dict[str, set[str]] = {}
    scanned_files = 0
    parse_errors: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*.json"))
        for path in paths:
            try:
                sources, composites = scan_document(path, conditional)
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                parse_errors.append(f"{path.relative_to(ROOT)}: {error}")
                continue
            scanned_files += 1
            used.update(sources)
            for composite, dependencies in composites.items():
                composite_dependencies.setdefault(composite, set()).update(dependencies)

    manifest = {
        "schema": "havenwild.universal_lpc_usage_manifest.v0_1",
        "generatedBy": "Build-UniversalLpcUsageManifestV167X.py",
        "authoritySchema": authority.get("schema"),
        "scannedFileCount": scanned_files,
        "shareAlikeSourceCount": len(used),
        "sources": [
            {
                "source": source,
                "modified": False,
                "modificationNote": "",
                "overridePath": None,
            }
            for source in sorted(used)
        ],
        "generatedComposites": [
            {
                "path": path,
                "sourceDependencies": sorted(dependencies),
            }
            for path, dependencies in sorted(composite_dependencies.items())
            if dependencies
        ],
        "parseErrors": parse_errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(
        f"Wrote {args.output} with {len(used):,} used CC-BY-SA sources "
        f"from {scanned_files:,} JSON documents"
    )
    if parse_errors:
        print(f"Warning: {len(parse_errors)} JSON documents could not be parsed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
