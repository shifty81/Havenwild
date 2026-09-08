#!/usr/bin/env python3
"""Create a deterministic ZIP from an already-prepared staging directory.

This helper replaces Windows PowerShell Compress-Archive for Havenwild project
packaging. It snapshots the staging file list first, verifies each file still
exists, and writes POSIX-style archive names so package output is stable across
Windows environments.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compression-level", type=int, default=9)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_stable(path: Path, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            before = path.stat()
            data = path.read_bytes()
            after = path.stat()
            if before.st_size != len(data) or after.st_size != len(data):
                raise OSError(f"file changed while packaging: {path}")
            return data
        except (FileNotFoundError, PermissionError, OSError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(0.15 * (attempt + 1))
    assert last_error is not None
    raise last_error


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    level = max(0, min(9, args.compression_level))

    if not source.is_dir():
        raise SystemExit(f"Staging directory does not exist: {source}")
    if output == source or source in output.parents:
        raise SystemExit("Output ZIP must live outside the staging directory.")

    files = sorted(
        (path for path in source.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source).as_posix().lower(),
    )
    if not files:
        raise SystemExit(f"Refusing to create an empty ZIP from: {source}")

    missing = [path for path in files if not path.is_file()]
    if missing:
        raise SystemExit(f"Staging file disappeared before ZIP creation: {missing[0]}")

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(output.name + f".tmp-{os.getpid()}")
    temp_output.unlink(missing_ok=True)

    try:
        with zipfile.ZipFile(
            temp_output,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=level,
            allowZip64=True,
        ) as archive:
            for path in files:
                relative = path.relative_to(source).as_posix()
                data = read_stable(path)
                info = zipfile.ZipInfo(relative)
                info.compress_type = zipfile.ZIP_DEFLATED
                # Keep a stable, ZIP-compatible timestamp instead of inheriting
                # machine-local source mtimes into transport identity.
                info.date_time = (2026, 1, 1, 0, 0, 0)
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=level)
        temp_output.replace(output)
    except Exception:
        temp_output.unlink(missing_ok=True)
        raise

    print(f"ZIP created: {output}")
    print(f"Files: {len(files)}")
    print(f"Bytes: {output.stat().st_size}")
    print(f"SHA-256: {sha256_file(output)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # packaging errors must be concise in Control Center logs
        print(f"ZIP packaging failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
