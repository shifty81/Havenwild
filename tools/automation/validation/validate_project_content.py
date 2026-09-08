#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_REVISION = "167Z62-project-content-scope-v5"

# These repository-root trees are generated, imported, archived, cached, or
# machine-local. They are not Havenwild-owned JSON authority and may contain
# third-party malformed fixtures or JSON-with-comments configuration files.
EXCLUDED_TOP_LEVEL = {
    ".git",
    ".havenwild",
    ".local",
    ".venv",
    "archive",
    "build",
    "imports",
    "logs",
    "node_modules",
    "target",
    "venv",
    "workspace",
}

# Third-party source mounts that intentionally remain under an owned top-level
# directory are excluded by exact case-insensitive repository-relative prefix.
EXCLUDED_PREFIXES = {
    ("assets", "source", "licensed"),
}

# Dependency/cache directories may also occur below otherwise owned trees.
EXCLUDED_ANYWHERE = {
    ".git",
    ".venv",
    "node_modules",
    "target",
    "venv",
}


def normalized_parts(root: Path, path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in path.relative_to(root).parts)


def should_skip(root: Path, path: Path) -> bool:
    parts = normalized_parts(root, path)
    if not parts:
        return False
    if parts[0] in EXCLUDED_TOP_LEVEL:
        return True
    if any(part in EXCLUDED_ANYWHERE for part in parts):
        return True
    return any(parts[: len(prefix)] == prefix for prefix in EXCLUDED_PREFIXES)


def validate_tree(root: Path) -> tuple[list[str], int, int]:
    issues: list[str] = []
    checked = 0
    skipped = 0

    for path in sorted(root.rglob("*.json")):
        if should_skip(root, path):
            skipped += 1
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            checked += 1
        except Exception as error:
            issues.append(f"{path.relative_to(root).as_posix()}: {error}")

    return issues, checked, skipped


def run_self_test() -> int:
    with TemporaryDirectory(prefix="havenwild-project-content-validator-") as directory:
        root = Path(directory)
        project_json = root / "content" / "valid.json"
        project_json.parent.mkdir(parents=True)
        project_json.write_text('{"valid": true}\n', encoding="utf-8")

        excluded = [
            root / ".havenwild" / "package-baseline.json",
            root / ".local" / "dependencies" / "fixture" / "bad.json",
            root / "IMPORTS" / "bad.json",
            root / "assets" / "source" / "licensed" / "fixture" / "bad.json",
            root / "node_modules" / "fixture" / "bad.json",
            root / "Build" / "HavenwildClient" / "content" / "bad.json",
            root / "BUILD" / "HavenwildEditor" / "content" / "bad.json",
            root / "content" / "nested" / "node_modules" / "bad.json",
        ]
        for path in excluded:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.parts[-2:] == (".havenwild", "package-baseline.json"):
                path.write_bytes(b"\xef\xbb\xbf{ intentionally invalid machine-local fixture")
            else:
                path.write_text("{ intentionally invalid fixture", encoding="utf-8")

        for path in excluded:
            assert should_skip(root, path), path
        issues, checked, skipped = validate_tree(root)
        assert not issues, issues
        assert checked == 1, checked
        assert skipped >= 1, skipped

        invalid_project_json = root / "content" / "invalid.json"
        invalid_project_json.write_text("{ invalid project json", encoding="utf-8")
        issues, checked, skipped = validate_tree(root)
        assert len(issues) == 1, issues
        assert issues[0].startswith("content/invalid.json:"), issues
        assert checked == 1, checked
        assert skipped >= 1, skipped

    print(f"Project content validator self-test passed ({VALIDATOR_REVISION})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Havenwild-owned JSON content only.")
    parser.add_argument("--self-test", action="store_true", help="Run ownership-scope regression tests.")
    parser.add_argument("--version", action="store_true", help="Print validator revision and exit.")
    args = parser.parse_args()

    if args.version:
        print(VALIDATOR_REVISION)
        return 0
    if args.self_test:
        return run_self_test()

    print(f"Havenwild project content validator: {VALIDATOR_REVISION}")
    issues, checked, skipped = validate_tree(ROOT)
    if issues:
        print("Content validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(
        f"Content validation passed ({checked} project JSON files checked; "
        f"{skipped} external/transient files skipped)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
