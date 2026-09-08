#!/usr/bin/env python3
"""Validate or acquire Havenwild's pinned ElizaWy/LPC dependency.

The raw LPC repository is a large authoring dependency (tens of thousands of
files). A compact Havenwild source rollup intentionally omits that tree. On the
first build this script acquires the exact locked commit into a local cache and
mounts it at ``assets/source/licensed/lpc_revised`` using a directory link.

Linking avoids copying the entire LPC tree into every clean source checkout.
Set ``HAVENWILD_LPC_SOURCE_MODE=copy`` to request a physical mirror instead.
``HAVENWILD_LPC_REPO`` may point at an existing LPC checkout, but it must not
point at Havenwild itself or any directory containing the project source root.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
SOURCE_MOUNT_PROVENANCE = ROOT / "WORKSPACE/generated/lpc/elizawy_source_mount_v167z38.json"
CACHE_ROOT = Path(os.environ.get("HAVENWILD_LPC_CACHE", ROOT / ".local/dependencies/lpc")).expanduser()
_TRUE_VALUES = {"1", "true", "yes", "on"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise RuntimeError(f"locked LPC file is not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def valid_locked_file(entry: dict) -> tuple[bool, str]:
    path = ROOT / entry["projectPath"]
    if not path.is_file():
        return False, f"missing {path}"
    actual_hash = sha256(path)
    if actual_hash.lower() != entry["sha256"].lower():
        return False, f"SHA-256 mismatch for {path}: {actual_hash}"
    if path.suffix.lower() == ".png":
        width, height = png_dimensions(path)
        expected = (int(entry["width"]), int(entry["height"]))
        if (width, height) != expected:
            return False, f"dimension mismatch for {path}: {(width, height)} != {expected}"
    return True, str(path)


def valid_full_source_tree(lock: dict) -> tuple[bool, str]:
    project_path = lock.get("fullSourceProjectPath")
    if not project_path:
        return True, "full source tree is not declared"
    root = ROOT / project_path
    if not root.is_dir():
        return False, f"missing full LPC source root {root}"
    for required in lock.get("requiredTopLevelPaths", []):
        if not (root / required).exists():
            return False, f"missing LPC top-level path {root / required}"
    for required in lock.get("requiredRootFiles", []):
        if not (root / required).is_file():
            return False, f"missing LPC root file {root / required}"
    for required in lock.get("requiredTerrainFiles", []):
        if not (root / required).is_file():
            return False, f"missing required LPC Terrain asset {root / required}"
    return True, str(root)


def checkout_head(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def write_source_mount_provenance(lock: dict, source_root: Path, mode: str) -> None:
    head = checkout_head(source_root)
    expected = str(lock["commit"])
    if head is not None and head.lower() != expected.lower():
        raise RuntimeError(f"LPC source commit mismatch: {head} != {expected}")
    verification_mode = "pinned_git_commit" if head is not None else "locked_export_structure_and_sha256"
    payload = {
        "schema": "havenwild.elizawy_source_mount_provenance.v167z38",
        "repository": lock["repository"],
        "expectedCommit": expected,
        "observedCommit": head,
        "verificationMode": verification_mode,
        "verified": True,
        "mount": lock["fullSourceProjectPath"],
        "mountMode": mode,
        "requiredTopLevelPathCount": len(lock.get("requiredTopLevelPaths", [])),
        "requiredRootFileCount": len(lock.get("requiredRootFiles", [])),
        "requiredTerrainFileCount": len(lock.get("requiredTerrainFiles", [])),
        "lockedFileCount": len(lock.get("lockedFiles", [])),
    }
    SOURCE_MOUNT_PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_MOUNT_PROVENANCE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def is_relative_to(path: Path, possible_parent: Path) -> bool:
    try:
        path.relative_to(possible_parent)
        return True
    except ValueError:
        return False


def validate_checkout_location(checkout: Path, destination: Path) -> None:
    checkout = checkout.resolve()
    destination = destination.resolve(strict=False)
    project_root = ROOT.resolve()

    if checkout == project_root:
        raise RuntimeError(
            "HAVENWILD_LPC_REPO points at the Havenwild project root. "
            "Unset it or point it at an ElizaWy/LPC checkout."
        )
    if is_relative_to(destination, checkout):
        raise RuntimeError(
            f"unsafe LPC source location: destination {destination} is inside checkout {checkout}; "
            "this would recursively copy the project into itself"
        )
    if is_relative_to(checkout, destination):
        raise RuntimeError(
            f"unsafe LPC source location: checkout {checkout} is inside destination {destination}"
        )


def cached_checkout_is_valid(checkout: Path, commit: str) -> bool:
    if not (checkout / ".git").is_dir():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return result.stdout.strip().lower() == commit.lower()


def ensure_checkout(repository: str, commit: str) -> Path:
    override = os.environ.get("HAVENWILD_LPC_REPO")
    if override:
        checkout = Path(override).expanduser().resolve()
        if not checkout.is_dir():
            raise RuntimeError(f"HAVENWILD_LPC_REPO is not a directory: {checkout}")
        head = checkout_head(checkout)
        if head is not None and head.lower() != commit.lower():
            raise RuntimeError(
                f"HAVENWILD_LPC_REPO is at commit {head}, expected pinned commit {commit}"
            )
        print(f"Using LPC checkout override: {checkout}")
        return checkout

    checkout = CACHE_ROOT / commit
    if cached_checkout_is_valid(checkout, commit):
        print(f"Using cached LPC checkout: {checkout}")
        return checkout
    if os.environ.get("HAVENWILD_OFFLINE", "").lower() in _TRUE_VALUES:
        raise RuntimeError("LPC dependency is missing or invalid and HAVENWILD_OFFLINE is enabled")
    if shutil.which("git") is None:
        raise RuntimeError("git is required to acquire the pinned LPC dependency")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    temp = CACHE_ROOT / f"{commit}.staging"
    remove_path(temp)
    temp.mkdir(parents=True)
    try:
        print(f"Fetching pinned LPC commit {commit} into {temp}")
        run("git", "-C", str(temp), "init")
        # The LPC tree contains deeply nested character variants. Enable Git's
        # Windows long-path handling before checkout so the pinned dependency
        # is complete rather than silently missing files.
        run("git", "-C", str(temp), "config", "core.longpaths", "true")
        run("git", "-C", str(temp), "remote", "add", "origin", repository)
        run("git", "-C", str(temp), "-c", "core.longpaths=true", "fetch", "--depth", "1", "origin", commit)
        run("git", "-C", str(temp), "checkout", "--detach", "FETCH_HEAD")
        remove_path(checkout)
        temp.rename(checkout)
    finally:
        remove_path(temp)
    return checkout


def path_entry_exists(path: Path) -> bool:
    """Return True for live or dangling filesystem entries.

    Path.exists() follows Windows directory junctions, so a dangling junction can
    report False even though its directory entry still blocks rename().  lstat()
    observes the entry itself and is therefore the correct repair predicate.
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
    if not path_entry_exists(path):
        return
    if is_directory_link(path):
        # A Windows junction is a directory reparse point.  os.rmdir removes the
        # junction itself without touching its target and also works when the
        # target has disappeared.  This is the key distinction from Path.exists().
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


def replace_directory_entry(staging: Path, destination: Path) -> None:
    """Move staging into place, repairing stale Windows destination entries."""
    last_error: OSError | None = None
    for attempt in range(1, 4):
        remove_path(destination)
        if path_entry_exists(destination):
            raise RuntimeError(f"unable to clear stale LPC destination: {destination}")
        try:
            staging.rename(destination)
            return
        except OSError as exc:
            last_error = exc
            # WinError 183 is ERROR_ALREADY_EXISTS.  A stale/dangling junction
            # may survive an earlier interrupted source mount, so retry after a
            # lexical-entry cleanup rather than abandoning the build.
            if getattr(exc, "winerror", None) != 183 or attempt == 3:
                raise
            print(
                f"WARNING: LPC mount destination reappeared during replace "
                f"(attempt {attempt}/3); clearing stale entry and retrying"
            )
            time.sleep(0.15 * attempt)
    if last_error is not None:
        raise last_error


def create_directory_link(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # Prefer PowerShell's structured junction API, then fall back to the
        # cmd.exe built-in. Both paths avoid copying the large dependency.
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        result = None
        if powershell:
            ps_command = (
                "New-Item -ItemType Junction "
                f"-Path '{str(destination).replace(chr(39), chr(39) * 2)}' "
                f"-Target '{str(source).replace(chr(39), chr(39) * 2)}' | Out-Null"
            )
            result = subprocess.run(
                [powershell, "-NoProfile", "-NonInteractive", "-Command", ps_command],
                capture_output=True,
                text=True,
            )
        if result is None or result.returncode != 0:
            junction_args = ["mklink", "/J", str(destination), str(source)]
            result = subprocess.run(
                ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline(junction_args)],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"unable to create LPC directory junction: {detail}")
    else:
        destination.symlink_to(source, target_is_directory=True)
    if not destination.is_dir():
        raise RuntimeError(f"LPC directory link was not created: {destination}")


def copy_tree_with_progress(checkout: Path, staging: Path) -> None:
    copied_files = 0
    copied_bytes = 0
    last_report = time.monotonic()

    def copy_file(source: str, destination: str) -> str:
        nonlocal copied_files, copied_bytes, last_report
        result = shutil.copy2(source, destination)
        copied_files += 1
        try:
            copied_bytes += Path(source).stat().st_size
        except OSError:
            pass
        now = time.monotonic()
        if copied_files % 2000 == 0 or now - last_report >= 5.0:
            print(
                f"  LPC mirror progress: {copied_files:,} files, "
                f"{copied_bytes / (1024 * 1024):.1f} MiB",
                flush=True,
            )
            last_report = now
        return result

    ignore = shutil.ignore_patterns(".git", ".github")
    # Preserve any repository symlinks rather than following them recursively.
    shutil.copytree(checkout, staging, ignore=ignore, copy_function=copy_file, symlinks=True)
    print(
        f"  LPC physical mirror complete: {copied_files:,} files, "
        f"{copied_bytes / (1024 * 1024):.1f} MiB",
        flush=True,
    )


def mount_full_source_tree(checkout: Path, lock: dict) -> str:
    project_path = lock.get("fullSourceProjectPath")
    if not project_path:
        return "not-declared"

    destination = ROOT / project_path
    validate_checkout_location(checkout, destination)
    staging = destination.with_name(destination.name + ".tmp")
    remove_path(staging)

    requested_mode = os.environ.get("HAVENWILD_LPC_SOURCE_MODE", "link").strip().lower()
    if requested_mode not in {"link", "copy"}:
        raise RuntimeError(
            "HAVENWILD_LPC_SOURCE_MODE must be either 'link' or 'copy', "
            f"not {requested_mode!r}"
        )

    mode_used = requested_mode
    if requested_mode == "link":
        try:
            create_directory_link(checkout, staging)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            if os.environ.get("HAVENWILD_LPC_LINK_REQUIRED", "").lower() in _TRUE_VALUES:
                raise
            print(f"WARNING: LPC directory link failed ({exc}); falling back to physical copy")
            remove_path(staging)
            copy_tree_with_progress(checkout, staging)
            mode_used = "copy"
    else:
        copy_tree_with_progress(checkout, staging)

    replace_directory_entry(staging, destination)
    print(f"LPC source {mode_used} ready: {destination} -> {checkout}")
    return mode_used


def same_file(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except OSError:
        return False


def copy_attribution(source_file: Path, destination_dir: Path) -> None:
    candidates: list[Path] = []
    for directory in (source_file.parent, source_file.parent.parent):
        if directory.is_dir():
            for pattern in ("credit*.txt", "Credit*.txt", "CREDIT*.txt"):
                candidates.extend(directory.glob(pattern))
    for source in sorted(set(candidates)):
        destination = destination_dir / source.name
        if destination.exists() and same_file(source, destination):
            continue
        shutil.copy2(source, destination)


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    invalid: list[tuple[dict | None, str]] = []
    ok, detail = valid_full_source_tree(lock)
    if not ok:
        invalid.append((None, detail))
    for entry in lock["lockedFiles"]:
        ok, detail = valid_locked_file(entry)
        if not ok:
            invalid.append((entry, detail))
    if not invalid:
        source_root = ROOT / lock["fullSourceProjectPath"]
        mode = "link" if is_directory_link(source_root) else "copy_or_export"
        write_source_mount_provenance(lock, source_root, mode)
        print(
            f"LPC dependency valid at pinned commit {lock['commit']} "
            f"({len(lock['lockedFiles'])} locked file(s))"
        )
        return 0

    print("LPC dependency requires repair:")
    for _, detail in invalid:
        print(f"  - {detail}")

    checkout = ensure_checkout(lock["repository"], lock["commit"])
    destination = ROOT / lock["fullSourceProjectPath"]
    validate_checkout_location(checkout, destination)
    mode_used = mount_full_source_tree(checkout, lock)

    for entry in lock["lockedFiles"]:
        source = checkout / entry["repositoryPath"]
        if not source.is_file():
            raise RuntimeError(f"pinned LPC checkout is missing {entry['repositoryPath']}")
        destination_file = ROOT / entry["projectPath"]
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        if not (destination_file.exists() and same_file(source, destination_file)):
            shutil.copy2(source, destination_file)
            copy_attribution(source, destination_file.parent)
            print(f"Promoted {entry['repositoryPath']} -> {entry['projectPath']}")
        else:
            print(f"Locked file available through mounted LPC source: {entry['repositoryPath']}")
        ok, detail = valid_locked_file(entry)
        if not ok:
            raise RuntimeError(detail)

    ok, detail = valid_full_source_tree(lock)
    if not ok:
        raise RuntimeError(detail)
    write_source_mount_provenance(lock, ROOT / lock["fullSourceProjectPath"], mode_used)
    print(f"LPC dependency repaired and verified at pinned commit {lock['commit']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            "ERROR: LPC dependency setup was cancelled. The partial staging path was left isolated "
            "and will be replaced automatically on the next run.",
            file=sys.stderr,
        )
        raise SystemExit(130)
    except (OSError, RuntimeError, subprocess.CalledProcessError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
