#!/usr/bin/env python3
"""Stage Havenwild application content without dependency repository internals."""
from __future__ import annotations

import argparse
import os
import shutil
import stat
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASSETS_ROOT = ROOT / "assets"
LICENSED_SOURCE_ROOT = ASSETS_ROOT / "source" / "licensed"
EXCLUDED_LICENSED_DIRECTORIES = {".git", "node_modules", "tests", "__pycache__"}
EXCLUDED_LICENSED_FILES = {"tsconfig.json"}


def _make_writable(path: str | os.PathLike[str]) -> None:
    candidate = Path(path)
    try:
        candidate.chmod(candidate.stat().st_mode | stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def _remove_readonly(function, path: str, _exc_info) -> None:
    _make_writable(path)
    function(path)


def remove_existing(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, onerror=_remove_readonly)
    else:
        _make_writable(path)
        path.unlink()


def _absolute_without_resolving(path: str | os.PathLike[str]) -> Path:
    """Return an absolute lexical path without dereferencing a junction/symlink."""
    return Path(os.path.abspath(os.fspath(path)))


def _is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


@lru_cache(maxsize=1)
def licensed_source_roots() -> tuple[Path, ...]:
    """Return lexical and resolved roots for mounted licensed repositories.

    Windows dependency mounts are directory junctions. ``Path.resolve()`` on the
    callback directory can therefore leave the project tree, which previously
    made the ignore callback believe that ``.git`` and dependency test fixtures
    were ordinary application content. Keep the lexical mount root and add each
    mounted repository's resolved target as an equivalent licensed root.
    """

    roots: list[Path] = [_absolute_without_resolving(LICENSED_SOURCE_ROOT)]
    if LICENSED_SOURCE_ROOT.is_dir():
        for child in LICENSED_SOURCE_ROOT.iterdir():
            if not child.is_dir():
                continue
            try:
                resolved = child.resolve()
            except OSError:
                continue
            if resolved not in roots:
                roots.append(resolved)
    return tuple(roots)


def is_under_licensed_source(directory: str | os.PathLike[str]) -> bool:
    current = _absolute_without_resolving(directory)
    candidates = [current]
    try:
        resolved = current.resolve()
    except OSError:
        resolved = current
    if resolved != current:
        candidates.append(resolved)
    return any(
        _is_within(candidate, licensed_root)
        for candidate in candidates
        for licensed_root in licensed_source_roots()
    )


def licensed_ignore(directory: str, names: list[str]) -> set[str]:
    """Exclude source-control and dependency development fixtures only."""
    if not is_under_licensed_source(directory):
        return set()
    ignored = {name for name in names if name.casefold() in EXCLUDED_LICENSED_DIRECTORIES}
    ignored.update(name for name in names if name.casefold() in EXCLUDED_LICENSED_FILES)
    return ignored


def stage_tree(source: Path, destination: Path, *, ignore=None) -> None:
    remove_existing(destination)
    shutil.copytree(source, destination, ignore=ignore)


def prune_staged_dependency_development(destination: Path) -> list[Path]:
    """Remove forbidden dependency-development paths as a final staging guard.

    The ignore callback prevents the normal copy. This second pass is required
    for Windows junction edge cases and for stale content produced by older
    staging implementations. It operates only inside the generated application
    bundle and never mutates the mounted dependency source.
    """

    licensed = destination / "assets" / "source" / "licensed"
    if not licensed.is_dir():
        return []

    removed: list[Path] = []
    for current, directories, files in os.walk(licensed, topdown=True):
        current_path = Path(current)
        for name in list(directories):
            if name.casefold() not in EXCLUDED_LICENSED_DIRECTORIES:
                continue
            target = current_path / name
            remove_existing(target)
            directories.remove(name)
            removed.append(target.relative_to(destination))
        for name in files:
            if name.casefold() not in EXCLUDED_LICENSED_FILES:
                continue
            target = current_path / name
            remove_existing(target)
            removed.append(target.relative_to(destination))
    return removed


def staged_forbidden_paths(destination: Path) -> list[Path]:
    licensed = destination / "assets" / "source" / "licensed"
    if not licensed.is_dir():
        return []
    return [
        path.relative_to(destination)
        for path in licensed.rglob("*")
        if path.name.casefold() in EXCLUDED_LICENSED_DIRECTORIES
        or (path.is_file() and path.name.casefold() in EXCLUDED_LICENSED_FILES)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    stage_tree(ROOT / "assets", destination / "assets", ignore=licensed_ignore)
    stage_tree(ROOT / "content", destination / "content")

    saves = destination / "WORKSPACE" / "saves"
    remove_existing(saves)
    saves.mkdir(parents=True, exist_ok=True)

    removed = prune_staged_dependency_development(destination)
    if removed:
        print(f"Pruned {len(removed)} dependency-development path(s) from staged application content")
        for path in removed[:10]:
            print(f"  - {path.as_posix()}")

    forbidden = staged_forbidden_paths(destination)
    if forbidden:
        raise SystemExit(
            "staged dependency-development files remain: "
            + ", ".join(path.as_posix() for path in forbidden[:10])
        )

    print(f"Staged filtered application content: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
