#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a short-name Havenwild recovery rollup from the latest patch backup snapshot."
    )
    parser.add_argument("--root", type=Path, default=None, help="Havenwild repository root")
    parser.add_argument(
        "--backup",
        default=None,
        help="Optional backup folder name or full path. Defaults to newest .havenwild/updates/backups snapshot.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional output ZIP path")
    parser.add_argument("--no-current", action="store_true", help="Do not include current counterparts")
    parser.add_argument("--no-logs", action="store_true", help="Do not include recent update/build logs")
    return parser.parse_args()


def normal_root(script: Path, requested: Path | None) -> Path:
    root = requested if requested is not None else script.resolve().parents[3]
    return Path(os.path.abspath(os.path.expanduser(str(root))))


def extended(path: Path | str) -> str:
    raw = os.path.abspath(str(path))
    if os.name != "nt":
        return raw
    if raw.startswith("\\\\?\\"):
        return raw
    if raw.startswith("\\\\"):
        return "\\\\?\\UNC\\" + raw[2:]
    return "\\\\?\\" + raw


def normal_display(path: Path | str) -> str:
    raw = str(path)
    if raw.startswith("\\\\?\\UNC\\"):
        return "\\\\" + raw[8:]
    if raw.startswith("\\\\?\\"):
        return raw[4:]
    return raw


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(extended(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def newest_backup(backup_root: Path) -> Path:
    root = extended(backup_root)
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Backup root does not exist: {backup_root}")
    candidates: list[tuple[float, str]] = []
    with os.scandir(root) as scan:
        for entry in scan:
            if entry.is_dir(follow_symlinks=False):
                candidates.append((entry.stat(follow_symlinks=False).st_mtime, normal_display(entry.path)))
    if not candidates:
        raise FileNotFoundError(f"No backup snapshots found under {backup_root}")
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return Path(candidates[0][1])


def resolve_backup(root: Path, requested: str | None) -> Path:
    backup_root = root / ".havenwild" / "updates" / "backups"
    if not requested:
        return newest_backup(backup_root)
    candidate = Path(os.path.expanduser(requested))
    if not candidate.is_absolute():
        candidate = backup_root / candidate
    if not os.path.isdir(extended(candidate)):
        raise FileNotFoundError(f"Backup snapshot does not exist: {candidate}")
    return candidate


def iter_files(root: Path) -> Iterable[tuple[Path, str]]:
    root_ext = extended(root)
    for current, dirs, files in os.walk(root_ext):
        dirs.sort()
        files.sort()
        for filename in files:
            full = os.path.join(current, filename)
            relative = os.path.relpath(full, root_ext).replace("\\", "/")
            if relative == ".." or relative.startswith("../"):
                continue
            yield Path(normal_display(full)), relative


def sanitize_entry(relative: str) -> str:
    parts = [part for part in relative.replace("\\", "/").split("/") if part not in ("", ".", "..")]
    return "/".join(parts)


def add_file(
    archive: zipfile.ZipFile,
    manifest_entries: list[dict[str, object]],
    source: Path,
    archive_name: str,
    role: str,
) -> None:
    archive_name = sanitize_entry(archive_name)
    if not archive_name:
        raise ValueError(f"Unsafe archive entry for {source}")
    source_ext = extended(source)
    size = os.path.getsize(source_ext)
    digest = sha256_file(source)
    with open(source_ext, "rb") as handle, archive.open(archive_name, "w") as target:
        shutil.copyfileobj(handle, target, length=1024 * 1024)
    manifest_entries.append(
        {
            "role": role,
            "archivePath": archive_name,
            "sourcePath": normal_display(source),
            "bytes": size,
            "sha256": digest,
        }
    )


def latest_files(directory: Path, pattern: str, count: int = 1) -> list[Path]:
    directory_ext = extended(directory)
    if not os.path.isdir(directory_ext):
        return []
    suffix = pattern.lstrip("*").lower()
    rows: list[tuple[float, Path]] = []
    with os.scandir(directory_ext) as scan:
        for entry in scan:
            if not entry.is_file(follow_symlinks=False):
                continue
            if suffix and not entry.name.lower().endswith(suffix):
                continue
            rows.append((entry.stat(follow_symlinks=False).st_mtime, Path(normal_display(entry.path))))
    rows.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in rows[:count]]


def matching_applied_patch(root: Path, backup: Path) -> Path | None:
    match = re.match(r"^\d{8}-\d{6}-(.+)$", backup.name)
    if not match:
        return None
    expected = match.group(1) + ".zip"
    applied_root = root / "artifacts" / "updates" / "applied"
    applied_ext = extended(applied_root)
    if not os.path.isdir(applied_ext):
        return None
    hits: list[tuple[float, Path]] = []
    for current, _, files in os.walk(applied_ext):
        for filename in files:
            if filename == expected:
                full = os.path.join(current, filename)
                hits.append((os.path.getmtime(full), Path(normal_display(full))))
    if not hits:
        return None
    hits.sort(key=lambda item: item[0], reverse=True)
    return hits[0][1]


def main() -> int:
    args = parse_args()
    script = Path(__file__)
    root = normal_root(script, args.root)
    backup = resolve_backup(root, args.backup)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = args.output
    if output is None:
        output = root / "artifacts" / "recovery" / f"Havenwild_Recovery_{stamp}.zip"
    elif not output.is_absolute():
        output = root / output
    output = Path(os.path.abspath(str(output)))
    os.makedirs(extended(output.parent), exist_ok=True)

    entries: list[dict[str, object]] = []
    current_added: set[str] = set()
    backup_files = list(iter_files(backup))

    with zipfile.ZipFile(extended(output), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, relative in backup_files:
            add_file(archive, entries, source, f"backup/{relative}", "backup")
            if not args.no_current:
                current = root / Path(relative)
                if os.path.isfile(extended(current)):
                    key = relative.replace("\\", "/")
                    if key not in current_added:
                        add_file(archive, entries, current, f"current/{key}", "current-counterpart")
                        current_added.add(key)

        applied = matching_applied_patch(root, backup)
        if applied is not None:
            add_file(archive, entries, applied, "applied/patch.zip", "matching-applied-patch")

        for relative in (
            "Cargo.toml",
            "Cargo.lock",
            "rust-toolchain.toml",
            "rust-toolchain",
            "HavenwildTools.cmd",
            "tools/control/ProjectCommandRegistry.ps1",
            "tools/control/InvokeRootPatchIntake.ps1",
        ):
            source = root / relative
            if os.path.isfile(extended(source)):
                add_file(archive, entries, source, f"project/{relative}", "project-context")

        if not args.no_logs:
            for category in ("updates", "builds", "diagnostics", "validation"):
                for log in latest_files(root / "logs" / category, ".log", 1):
                    add_file(archive, entries, log, f"logs/{category}/{log.name}", "recent-log")

        manifest = {
            "schema": "havenwild.recovery_rollup.v1",
            "createdAtUtc": datetime.now(timezone.utc).isoformat(),
            "repositoryRoot": normal_display(root),
            "backupSnapshot": normal_display(backup),
            "backupSnapshotName": backup.name,
            "backupFileCount": len(backup_files),
            "currentCounterpartsIncluded": not args.no_current,
            "recentLogsIncluded": not args.no_logs,
            "entries": entries,
        }
        archive.writestr("RECOVERY_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr(
            "README.txt",
            "Havenwild recovery rollup\n"
            "=========================\n"
            "backup/  = files captured before the selected root patch overwrote them\n"
            "current/ = current repository counterparts for those same relative paths\n"
            "applied/patch.zip = matching consumed root patch when it could be located\n"
            "project/ = small project/control metadata useful for recovery\n"
            "logs/    = latest update/build/diagnostic/validation logs\n"
            "RECOVERY_MANIFEST.json records original paths, sizes, and SHA-256 hashes.\n",
        )

    digest = sha256_file(output)
    sidecar = Path(str(output) + ".sha256")
    with open(extended(sidecar), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {output.name}\n")
    latest = output.parent / "LATEST_RECOVERY_ROLLUP.txt"
    with open(extended(latest), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"ZIP={normal_display(output)}\nSHA256={digest}\nBACKUP={normal_display(backup)}\n")

    print(f"RECOVERY ROLLUP: {normal_display(output)}")
    print(f"RECOVERY SHA-256: {digest}")
    print(f"BACKUP SNAPSHOT: {normal_display(backup)}")
    print(f"BACKUP FILES: {len(backup_files)}")
    print(f"MANIFEST ENTRIES: {len(entries)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RECOVERY ROLLUP FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
