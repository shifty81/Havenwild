#!/usr/bin/env python3
"""Normalize machine-local Havenwild workspace layout safely.

This preflight repairs known case-only root names, merges the retired ``.logs``
tree, removes known transient upgrade files, and best-effort prunes development-
only dependency internals from generated application bundles. Cleanup of
``Build/`` is never allowed to block source validation or compilation.
"""
from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CANONICAL_CASE_DIRS = ("tools", "docs")
LEGACY_SCRIPT_ROUTES = {
    "Validate-LpcProjectFoundationPass167Z40.py":
        "tools/automation/validation/checks/assets/Validate-LpcProjectFoundationPass167Z40.py",
    "Validate-LpcFoundationSummaryRepairPass167Z41.py":
        "tools/automation/validation/checks/assets/Validate-LpcFoundationSummaryRepairPass167Z41.py",
    "Validate-UlpcPartialActionGeometryPass167Z42.py":
        "tools/automation/validation/checks/characters/Validate-UlpcPartialActionGeometryPass167Z42.py",
    "Validate-WorldCreationHousingFamilyPass167Z39.py":
        "tools/automation/validation/checks/world/Validate-WorldCreationHousingFamilyPass167Z39.py",
}
KNOWN_TRANSIENT_FILES = (
    "crates/haven_world/src/autotile/shoreline_resolver_tests.rs.tmp",
    "manifests/ROLLUP_CARGO_CHECK.log",
    "manifests/ROLLUP_FMT_CHECK.log",
)


def _make_writable(path: str | os.PathLike[str]) -> None:
    """Clear the Windows read-only bit while preserving useful permissions."""
    candidate = Path(path)
    try:
        current = candidate.stat().st_mode
        candidate.chmod(current | stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def _remove_readonly(function, path: str, _exc_info) -> None:
    """``shutil.rmtree`` callback for Git packs and other read-only files."""
    _make_writable(path)
    function(path)


def force_remove(path: Path) -> tuple[bool, str | None]:
    """Remove a file/tree after clearing read-only attributes.

    Returns ``(removed, warning)``. Generated build-output cleanup is
    best-effort because locked antivirus/indexer handles must not prevent the
    source build from continuing.
    """
    if not path.exists() and not path.is_symlink():
        return False, None
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, onerror=_remove_readonly)
        else:
            _make_writable(path)
            path.unlink()
        return True, None
    except OSError as exc:
        return False, f"{path.relative_to(ROOT).as_posix()}: {exc}"


def normalize_case_only_directory(canonical: str) -> bool:
    matches = [entry for entry in ROOT.iterdir() if entry.is_dir() and entry.name.casefold() == canonical.casefold()]
    if not matches:
        return False
    if len(matches) > 1:
        names = ", ".join(sorted(entry.name for entry in matches))
        raise RuntimeError(f"case-colliding root directories require manual repair: {names}")
    source = matches[0]
    if source.name == canonical:
        return False

    temporary = ROOT / f".havenwild-casefix-{canonical}-{os.getpid()}"
    if temporary.exists():
        raise RuntimeError(f"temporary normalization path already exists: {temporary}")
    source.rename(temporary)
    temporary.rename(ROOT / canonical)
    print(f"Normalized root directory casing: {source.name} -> {canonical}")
    return True


def merge_tree(source: Path, destination: Path) -> int:
    moved = 0
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*"), key=lambda item: len(item.parts)):
        if path.is_dir():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if path.read_bytes() == target.read_bytes():
                path.unlink()
                continue
            stem, suffix = target.stem, target.suffix
            index = 1
            while target.exists():
                target = target.with_name(f"{stem}.legacy-{index}{suffix}")
                index += 1
        shutil.move(str(path), str(target))
        moved += 1
    removed, warning = force_remove(source)
    if warning:
        print(f"WARNING: unable to remove empty legacy log tree: {warning}")
    return moved



def _route_legacy_file(source: Path, destination: Path, archive_root: Path) -> tuple[bool, str | None]:
    """Move one retired SCRIPTS file without replacing canonical active source."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        try:
            if source.read_bytes() == destination.read_bytes():
                source.unlink()
                return True, None
        except OSError as exc:
            return False, f"{source.relative_to(ROOT).as_posix()}: {exc}"
        archive_target = archive_root / source.relative_to(ROOT / "SCRIPTS")
        archive_target.parent.mkdir(parents=True, exist_ok=True)
        suffix = 1
        candidate = archive_target
        while candidate.exists():
            candidate = archive_target.with_name(
                f"{archive_target.stem}.conflict-{suffix}{archive_target.suffix}"
            )
            suffix += 1
        shutil.move(str(source), str(candidate))
        return True, None
    shutil.move(str(source), str(destination))
    return True, None


def normalize_legacy_scripts() -> bool:
    """Migrate the retired root SCRIPTS tree into canonical tooling folders.

    The validator framework package is merged into ``tools/automation/validation``.
    Known active pass validators receive stable domain-specific locations. Any
    unrecognized legacy script is retained under ``tools/archive`` rather than
    left in the repository root.
    """
    legacy_root = ROOT / "SCRIPTS"
    if not legacy_root.is_dir():
        return False

    changed = False
    warnings: list[str] = []
    archive_root = ROOT / "tools/archive/legacy_scripts/pass167z43_layout_migration"

    framework_root = legacy_root / "validation"
    if framework_root.is_dir():
        for source in sorted(framework_root.rglob("*")):
            if not source.is_file():
                continue
            if "__pycache__" in source.parts or source.suffix.lower() in {".pyc", ".pyo"}:
                source.unlink()
                changed = True
                continue
            destination = ROOT / "tools/automation/validation" / source.relative_to(framework_root)
            moved, warning = _route_legacy_file(source, destination, archive_root / "validation_conflicts")
            changed = moved or changed
            if warning:
                warnings.append(warning)
        removed, warning = force_remove(framework_root)
        changed = removed or changed
        if warning:
            warnings.append(warning)

    for filename, relative_destination in LEGACY_SCRIPT_ROUTES.items():
        source = legacy_root / filename
        if not source.is_file():
            continue
        moved, warning = _route_legacy_file(source, ROOT / relative_destination, archive_root / "validator_conflicts")
        changed = moved or changed
        if warning:
            warnings.append(warning)

    for source in sorted(legacy_root.rglob("*")):
        if not source.is_file():
            continue
        destination = archive_root / "unclassified" / source.relative_to(legacy_root)
        moved, warning = _route_legacy_file(source, destination, archive_root / "unclassified_conflicts")
        changed = moved or changed
        if warning:
            warnings.append(warning)

    removed, warning = force_remove(legacy_root)
    changed = removed or changed
    if warning:
        warnings.append(warning)

    if changed:
        print("Migrated retired root SCRIPTS tooling into tools/automation and tools/archive")
    for item in warnings:
        print(f"WARNING: legacy script migration deferred: {item}")
    return bool(changed or warnings)

def normalize_legacy_logs() -> bool:
    legacy = ROOT / ".logs"
    if not legacy.exists():
        return False
    current = ROOT / "logs"
    if current.exists():
        moved = merge_tree(legacy, current)
        print(f"Merged legacy .logs into logs ({moved} file(s) moved)")
    else:
        legacy.rename(current)
        print("Renamed legacy .logs -> logs")
    return True


def remove_known_transients() -> bool:
    removed = []
    warnings = []
    for relative in KNOWN_TRANSIENT_FILES:
        did_remove, warning = force_remove(ROOT / relative)
        if did_remove:
            removed.append(relative)
        if warning:
            warnings.append(warning)
    if removed:
        print(f"Removed {len(removed)} known transient upgrade file(s)")
        for relative in removed:
            print(f"  - {relative}")
    for warning in warnings:
        print(f"WARNING: transient cleanup deferred: {warning}")
    return bool(removed or warnings)


def prune_staged_dependency_development_files() -> bool:
    """Best-effort cleanup for app bundles produced before filtered staging."""
    build_root = ROOT / "Build"
    if not build_root.is_dir():
        return False

    candidates: set[Path] = set()
    for application_root in sorted(build_root.glob("Havenwild*")):
        licensed_root = application_root / "assets" / "source" / "licensed"
        universal_lpc = licensed_root / "universal_lpc_generator"
        candidates.update(
            {
                universal_lpc / ".git",
                universal_lpc / "node_modules",
                universal_lpc / "tests",
                universal_lpc / "tsconfig.json",
            }
        )
        if licensed_root.is_dir():
            candidates.update(path for path in licensed_root.rglob(".git") if path.is_dir())

    removed: list[str] = []
    warnings: list[str] = []
    for candidate in sorted(candidates, key=lambda item: len(item.parts), reverse=True):
        did_remove, warning = force_remove(candidate)
        if did_remove:
            removed.append(candidate.relative_to(ROOT).as_posix())
        if warning:
            warnings.append(warning)

    if removed:
        print(f"Pruned {len(removed)} dependency-development path(s) from generated app bundles")
        for relative in sorted(removed):
            print(f"  - {relative}")
    for warning in warnings:
        print(f"WARNING: staged dependency cleanup deferred; build may continue: {warning}")
    return bool(removed or warnings)


def main() -> int:
    changed = False
    for canonical in CANONICAL_CASE_DIRS:
        changed = normalize_case_only_directory(canonical) or changed
    changed = normalize_legacy_scripts() or changed
    changed = normalize_legacy_logs() or changed
    changed = remove_known_transients() or changed
    changed = prune_staged_dependency_development_files() or changed
    if not changed:
        print("Workspace layout already normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
