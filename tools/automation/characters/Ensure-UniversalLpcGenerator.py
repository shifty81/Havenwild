#!/usr/bin/env python3
"""Acquire and mount the complete locked Universal LPC character repository.

The repository is the source authority for Havenwild character bodies, heads,
clothing, equipment, tools, weapons, shields, and character animation layers.
The complete source tree remains a local dependency so incremental patches and
source rollups do not duplicate 140+ MB of third-party source data.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "content/assets/intake/universal_lpc_generator_source_lock_v0_1.json"
STATE_PATH = ROOT / "WORKSPACE/generated/universal_lpc_source_state.json"
TRUE = {"1", "true", "yes", "on"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_entry_exists(path: Path) -> bool:
    """Return True for live or dangling filesystem entries.

    Path.exists() follows Windows junction targets. A dangling junction can
    therefore report False while its directory entry still occupies the mount
    path and makes mklink/copytree fail with ERROR_ALREADY_EXISTS.
    """
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def is_directory_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None:
        try:
            if is_junction():
                return True
        except OSError:
            pass
    if os.name == "nt":
        try:
            attributes = path.lstat().st_file_attributes
        except (AttributeError, FileNotFoundError, OSError):
            return False
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
        directory = getattr(stat, "FILE_ATTRIBUTE_DIRECTORY", 0x0010)
        return bool(attributes & reparse and attributes & directory)
    return False


def remove_path(path: Path) -> None:
    """Remove only the mount entry when path is a directory link/junction."""
    if not path_entry_exists(path):
        return
    if is_directory_link(path):
        try:
            os.rmdir(path)
        except OSError:
            path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    if path_entry_exists(path):
        raise RuntimeError(f"filesystem entry still exists after removal: {path}")


def validate_source(source: Path, lock: dict) -> None:
    if not source.is_dir():
        raise RuntimeError(f"Universal LPC source root is missing: {source}")
    for relative in lock["requiredTopLevelPaths"]:
        if not (source / relative).exists():
            raise RuntimeError(f"Universal LPC source is missing {relative}")


def safe_extract(archive: Path, destination: Path, expected_root: str) -> Path:
    staging = destination.with_name(destination.name + ".staging")
    remove_path(staging)
    staging.mkdir(parents=True)
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            target = (staging / item.filename).resolve()
            if not str(target).startswith(str(staging.resolve()) + os.sep):
                raise RuntimeError(f"unsafe archive path: {item.filename}")
        bundle.extractall(staging)
    extracted = staging / expected_root
    if not extracted.is_dir():
        raise RuntimeError(f"archive did not contain expected root {expected_root}")
    remove_path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    extracted.rename(destination)
    remove_path(staging)
    return destination


def _same_directory(source: Path, destination: Path) -> bool:
    if not destination.exists():
        return False
    try:
        return os.path.samefile(source, destination)
    except OSError:
        return False


def _copy_mount(source: Path, destination: Path) -> str:
    """Create a physical local mount when Windows junction creation is unavailable."""
    remove_path(destination)
    shutil.copytree(source, destination, copy_function=shutil.copy2)
    return "physical_copy"


def create_link(source: Path, destination: Path) -> str:
    """Mount source at destination and return the mount mode.

    Passing one pre-quoted command string through ``cmd.exe /s /c`` causes
    Python's Windows argument encoder to emit backslash-escaped quotes.
    ``cmd.exe`` does not treat those backslashes as quote escapes, which makes
    paths containing spaces fail with Win32 error 123.  Supplying each mklink
    token as its own argument produces the required command line instead.
    """
    source = source.resolve()
    if _same_directory(source, destination):
        return "existing_mount"

    remove_path(destination)
    if path_entry_exists(destination):
        raise RuntimeError(f"unable to clear stale Universal LPC mount: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        result = None
        junction_error = ""
        for attempt in range(1, 4):
            result = subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    os.fspath(destination),
                    os.fspath(source),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and destination.is_dir():
                return "junction"
            junction_error = (result.stderr or result.stdout).strip()
            if not path_entry_exists(destination) or attempt == 3:
                break
            print(
                "WARNING: Universal LPC mount destination reappeared during junction creation "
                f"(attempt {attempt}/3); clearing stale entry and retrying"
            )
            remove_path(destination)

        try:
            mode = _copy_mount(source, destination)
        except Exception as copy_error:
            raise RuntimeError(
                "Universal LPC mount failed. "
                f"Junction error: {junction_error or 'unknown mklink failure'}. "
                f"Physical-copy fallback error: {copy_error}"
            ) from copy_error
        print(
            "WARNING: Universal LPC junction creation failed; "
            f"using physical local mount instead ({junction_error or 'unknown mklink failure'})"
        )
        return mode

    destination.symlink_to(source, target_is_directory=True)
    return "symlink"




def run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=os.fspath(cwd) if cwd is not None else None,
        check=True,
        capture_output=True,
        text=True,
    )


def checkout_head(checkout: Path) -> str | None:
    if not (checkout / ".git").is_dir():
        return None
    try:
        result = run_git("-C", os.fspath(checkout), "rev-parse", "HEAD")
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def fetch_pinned_repository(lock: dict, destination: Path) -> Path:
    repository = lock["repository"]
    commit = lock["commit"]
    if os.environ.get("HAVENWILD_OFFLINE", "").lower() in TRUE:
        raise RuntimeError(
            "Universal LPC dependency is missing and HAVENWILD_OFFLINE is enabled"
        )
    if shutil.which("git") is None:
        raise RuntimeError(
            "git is required to acquire the pinned Universal LPC dependency"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + ".staging")
    remove_path(staging)
    staging.mkdir(parents=True)
    try:
        print(f"Fetching pinned Universal LPC commit {commit} into {staging}")
        run_git("init", cwd=staging)
        run_git("config", "core.longpaths", "true", cwd=staging)
        run_git("remote", "add", "origin", repository, cwd=staging)
        run_git(
            "-c",
            "core.longpaths=true",
            "fetch",
            "--depth",
            "1",
            "origin",
            commit,
            cwd=staging,
        )
        run_git("checkout", "--detach", "FETCH_HEAD", cwd=staging)
        head = checkout_head(staging)
        if head is None or head.lower() != commit.lower():
            raise RuntimeError(
                f"Universal LPC checkout resolved to {head or 'unknown'}, expected {commit}"
            )
        validate_source(staging, lock)
        remove_path(destination)
        staging.rename(destination)
    finally:
        remove_path(staging)
    return destination


def discover_archive(lock: dict) -> Path | None:
    override = os.environ.get("HAVENWILD_ULPC_ARCHIVE")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser())
    name = lock["archiveFileName"]
    candidates.extend(
        [
            ROOT / name,
            ROOT / "IMPORTS" / name,
            ROOT / "dependencies" / name,
            ROOT / "assets/source/archives" / name,
            ROOT / ".local/imports" / name,
            ROOT.parent / name,
        ]
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    return None


def park_root_archive(lock: dict) -> Path | None:
    """Move the locked archive out of the repository root after use.

    The control-center workflow historically told developers to place the
    Universal LPC ZIP beside ``Cargo.toml``.  That is convenient for first
    bootstrap but conflicts with the normalized five-file root contract.
    Once the archive has been verified/extracted, keep it under ``IMPORTS``
    so subsequent validation and packaging remain deterministic.
    """
    root_archive = ROOT / lock["archiveFileName"]
    if not root_archive.is_file():
        return None

    actual = sha256(root_archive)
    expected = lock["archiveSha256"].lower()
    if actual.lower() != expected:
        raise RuntimeError(f"Universal LPC root archive hash mismatch: {actual}")

    imports = ROOT / "IMPORTS"
    imports.mkdir(parents=True, exist_ok=True)
    parked = imports / root_archive.name
    if parked.exists():
        parked_hash = sha256(parked)
        if parked_hash.lower() != expected:
            raise RuntimeError(
                f"Cannot park Universal LPC archive because {parked} has hash {parked_hash}"
            )
        root_archive.unlink()
        print(f"Removed duplicate root archive; locked copy already exists at {parked}")
    else:
        root_archive.replace(parked)
        print(f"Moved locked Universal LPC archive out of root: {parked}")
    return parked


def source_counts(source: Path) -> tuple[int, int, int]:
    spritesheets = sum(1 for path in (source / "spritesheets").rglob("*.png") if path.is_file())
    definitions = sum(1 for path in (source / "sheet_definitions").rglob("*.json") if path.is_file())
    palettes = sum(1 for path in (source / "palette_definitions").rglob("*.json") if path.is_file())
    return spritesheets, definitions, palettes


def write_state(source: Path, lock: dict, acquisition: str, mount_mode: str) -> None:
    spritesheets, definitions, palettes = source_counts(source)
    if spritesheets != 88235 or definitions != 768:
        raise RuntimeError(
            "Universal LPC repository inventory changed: "
            f"{spritesheets} spritesheets, {definitions} definitions"
        )
    state = {
        "schema": "havenwild.universal_lpc_source_state.v167z7",
        "repository": lock["repository"],
        "commit": lock["commit"],
        "archiveSha256": lock["archiveSha256"],
        "sourceRoot": str(source.resolve()),
        "mountProjectPath": lock["mountProjectPath"],
        "acquisition": acquisition,
        "mountMode": mount_mode,
        "spritesheetFiles": spritesheets,
        "sheetDefinitionFiles": definitions,
        "paletteDefinitionFiles": palettes,
        "completeRepositoryMounted": True,
        "visualAuthority": [
            "character bodies and heads",
            "hair and facial layers",
            "clothing and armor",
            "tools, weapons, shields, and held equipment",
            "character animation layers",
        ],
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    commit = lock["commit"]
    destination = ROOT / lock["localCachePath"]
    mount = ROOT / lock["mountProjectPath"]

    repo_override = os.environ.get("HAVENWILD_ULPC_REPO")
    if repo_override:
        source = Path(repo_override).expanduser().resolve()
        validate_source(source, lock)
        mount_mode = create_link(source, mount)
        write_state(source, lock, "repository_override", mount_mode)
        park_root_archive(lock)
        print(f"Mounted complete Universal LPC repository from {source}")
        return 0

    if destination.is_dir():
        validate_source(destination, lock)
        mount_mode = create_link(destination.resolve(), mount)
        if not STATE_PATH.is_file():
            write_state(destination, lock, "local_cache", mount_mode)
        park_root_archive(lock)
        print(f"Complete Universal LPC repository valid at {commit}")
        return 0

    if mount.is_dir():
        validate_source(mount, lock)
        write_state(mount, lock, "existing_mount", "existing_mount")
        park_root_archive(lock)
        print(f"Complete Universal LPC repository mount valid at {commit}")
        return 0

    archive = discover_archive(lock)
    if archive is not None:
        actual = sha256(archive)
        if actual.lower() != lock["archiveSha256"].lower():
            raise RuntimeError(f"Universal LPC archive hash mismatch: {actual}")
        source = safe_extract(
            archive,
            destination,
            "Universal-LPC-Spritesheet-Character-Generator-master",
        )
        validate_source(source, lock)
        mount_mode = create_link(source.resolve(), mount)
        write_state(source, lock, "locked_archive", mount_mode)
        park_root_archive(lock)
        print(f"Extracted and mounted complete Universal LPC repository at {commit}")
        return 0

    try:
        source = fetch_pinned_repository(lock, destination)
        mount_mode = create_link(source.resolve(), mount)
        write_state(source, lock, "pinned_git_fetch", mount_mode)
        print(f"Fetched and mounted complete Universal LPC repository at {commit}")
        return 0
    except Exception as fetch_error:
        if os.environ.get("HAVENWILD_ULPC_STRICT", "").lower() in TRUE:
            raise RuntimeError(
                "Complete Universal LPC source is required and automatic pinned Git acquisition failed. "
                f"{fetch_error}. You may alternatively place {lock['archiveFileName']} under IMPORTS/ "
                "or set HAVENWILD_ULPC_ARCHIVE/HAVENWILD_ULPC_REPO."
            ) from fetch_error
        print(f"INFO Complete Universal LPC source is not mounted: {fetch_error}")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
