#!/usr/bin/env python3
"""Restore and verify Havenwild's pinned [LPC] Terrains V7 source package.

The package is external CC-BY-SA content and is intentionally omitted from Git.
Clean checkouts hydrate the exact known-good source files from OpenGameArt (or a
local override), verify every required file by SHA-256, preserve attribution,
and copy the verified subset into content/assets/lpc/source/lpc-terrains-v7.

Environment overrides:
  HAVENWILD_LPC_TERRAIN_V7_ARCHIVE  path to lpc-terrains.zip
  HAVENWILD_LPC_TERRAIN_V7_SOURCE   path to an extracted source directory
  HAVENWILD_LPC_TERRAIN_V7_CACHE    alternate local cache root
  HAVENWILD_OFFLINE=1               never use the network
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "content/assets/intake/lpc_terrain_v7_source_lock_v0_1.json"
PROVENANCE_PATH = ROOT / "WORKSPACE/generated/dependencies/lpc_terrain_v7_source_v1.json"
_TRUE = {"1", "true", "yes", "on"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError(f"LPC Terrains V7 lock is missing: {LOCK_PATH}")
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8-sig"))
    if data.get("schema") != "havenwild.external_dependency_lock.v1":
        raise RuntimeError(f"Unsupported LPC Terrains V7 lock schema: {data.get('schema')!r}")
    return data


def required_entries(lock: dict) -> list[dict]:
    entries = list((lock.get("verification") or {}).get("requiredFiles") or [])
    if not entries:
        raise RuntimeError("LPC Terrains V7 lock contains no required file fingerprints")
    return entries


def validate_source(root: Path, lock: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for entry in required_entries(lock):
        rel = str(entry["path"])
        path = root / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        size = path.stat().st_size
        expected_size = int(entry["bytes"])
        if size != expected_size:
            errors.append(f"size mismatch {rel}: {size} != {expected_size}")
            continue
        actual = sha256(path)
        expected = str(entry["sha256"]).lower()
        if actual.lower() != expected:
            errors.append(f"SHA-256 mismatch {rel}: {actual} != {expected}")
    return not errors, errors


def find_source_root(extracted: Path, lock: dict) -> Path:
    names = [str(e["path"]) for e in required_entries(lock)]
    # First try archive root, then every directory containing the most unique
    # core file. This is robust to archives that add or remove a wrapper folder.
    candidates = [extracted]
    anchor = "terrain-map-v7.tsx"
    candidates.extend(p.parent for p in extracted.rglob(anchor))
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        if all((candidate / name).is_file() for name in names):
            ok, _ = validate_source(candidate, lock)
            if ok:
                return candidate
    details = []
    for candidate in list(seen)[:12]:
        missing = [name for name in names if not (candidate / name).is_file()]
        if len(missing) < len(names):
            details.append(f"{candidate}: missing {', '.join(missing[:4])}")
    suffix = "\n  " + "\n  ".join(details) if details else ""
    raise RuntimeError(
        "Downloaded LPC Terrains archive does not contain the locked known-good V7 source set."
        + suffix
    )


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    dest_resolved = destination.resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"unsafe archive entry: {info.filename}")
            target = (destination / name).resolve()
            try:
                target.relative_to(dest_resolved)
            except ValueError as exc:
                raise RuntimeError(f"archive entry escapes extraction root: {info.filename}") from exc
        zf.extractall(destination)


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Havenwild-Dependency-Bootstrap/CC8E11",
            "Accept": "application/zip,application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with destination.open("wb") as out:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
    if not zipfile.is_zipfile(destination):
        raise RuntimeError(f"download is not a ZIP archive: {url}")


def install_verified_subset(source: Path, destination: Path, lock: dict) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + ".staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        for entry in required_entries(lock):
            rel = Path(str(entry["path"]))
            src = source / rel
            dst = staging / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        ok, errors = validate_source(staging, lock)
        if not ok:
            raise RuntimeError("staged LPC Terrains V7 verification failed:\n - " + "\n - ".join(errors))
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def write_provenance(lock: dict, source_kind: str, source_value: str, destination: Path) -> None:
    payload = {
        "schema": "havenwild.external_dependency_provenance.v1",
        "id": lock["id"],
        "verified": True,
        "verificationMode": (lock.get("verification") or {}).get("mode"),
        "sourceKind": source_kind,
        "source": source_value,
        "sourcePage": lock.get("sourcePage"),
        "projectMount": str(destination.relative_to(ROOT)).replace("\\", "/"),
        "attributionFile": lock.get("attributionFile"),
        "requiredFileCount": len(required_entries(lock)),
        "verifiedFiles": [
            {
                "path": str(e["path"]),
                "sha256": str(e["sha256"]),
                "bytes": int(e["bytes"]),
            }
            for e in required_entries(lock)
        ],
    }
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    lock = load_lock()
    destination = ROOT / str(lock["projectMount"])
    ok, errors = validate_source(destination, lock)
    if ok:
        print(
            f"LPC Terrains V7 source ready: {destination.relative_to(ROOT)} "
            f"({len(required_entries(lock))} locked files)"
        )
        return 0

    print("LPC Terrains V7 source requires restore:")
    for error in errors[:12]:
        print(f"  - {error}")

    source_override = os.environ.get("HAVENWILD_LPC_TERRAIN_V7_SOURCE", "").strip()
    if source_override:
        source = Path(source_override).expanduser().resolve()
        ok, override_errors = validate_source(source, lock)
        if not ok:
            raise RuntimeError(
                "HAVENWILD_LPC_TERRAIN_V7_SOURCE is not the locked source set:\n - "
                + "\n - ".join(override_errors)
            )
        install_verified_subset(source, destination, lock)
        write_provenance(lock, "source_override", str(source), destination)
        print(f"LPC Terrains V7 restored from source override -> {destination}")
        return 0

    cache_root = Path(
        os.environ.get(
            "HAVENWILD_LPC_TERRAIN_V7_CACHE",
            ROOT / str(lock.get("cacheRoot") or ".local/dependencies/lpc_terrains_v7"),
        )
    ).expanduser()
    cache_root.mkdir(parents=True, exist_ok=True)
    verified_cache = cache_root / "verified_source"
    ok, _ = validate_source(verified_cache, lock)
    if ok:
        install_verified_subset(verified_cache, destination, lock)
        write_provenance(lock, "verified_cache", str(verified_cache), destination)
        print(f"LPC Terrains V7 restored from verified cache -> {destination}")
        return 0

    archive_override = os.environ.get("HAVENWILD_LPC_TERRAIN_V7_ARCHIVE", "").strip()
    archive: Path | None = None
    source_kind = ""
    source_value = ""

    if archive_override:
        archive = Path(archive_override).expanduser().resolve()
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            raise RuntimeError(f"HAVENWILD_LPC_TERRAIN_V7_ARCHIVE is not a readable ZIP: {archive}")
        source_kind = "archive_override"
        source_value = str(archive)
    else:
        if os.environ.get("HAVENWILD_OFFLINE", "").strip().lower() in _TRUE:
            raise RuntimeError(
                "LPC Terrains V7 is missing and HAVENWILD_OFFLINE is enabled. "
                "Provide HAVENWILD_LPC_TERRAIN_V7_ARCHIVE or HAVENWILD_LPC_TERRAIN_V7_SOURCE."
            )
        failures: list[str] = []
        download_path = cache_root / str(lock.get("archiveFileName") or "lpc-terrains.zip")
        for url in lock.get("archiveUrls") or []:
            for attempt in range(1, 4):
                temporary = cache_root / f"download-{attempt}.tmp"
                temporary.unlink(missing_ok=True)
                try:
                    print(f"Downloading LPC Terrains V7 (attempt {attempt}/3): {url}")
                    download(str(url), temporary)
                    temporary.replace(download_path)
                    archive = download_path
                    source_kind = "download"
                    source_value = str(url)
                    break
                except (OSError, RuntimeError, urllib.error.URLError) as exc:
                    failures.append(f"{url} attempt {attempt}: {exc}")
                    temporary.unlink(missing_ok=True)
                    if attempt < 3:
                        time.sleep(attempt * 1.5)
            if archive is not None:
                break
        if archive is None:
            raise RuntimeError(
                "Unable to download LPC Terrains V7 archive:\n - " + "\n - ".join(failures)
            )

    with tempfile.TemporaryDirectory(prefix="havenwild-lpc-terrain-v7-") as td:
        extracted = Path(td)
        safe_extract(archive, extracted)
        source_root = find_source_root(extracted, lock)

        if verified_cache.exists():
            shutil.rmtree(verified_cache)
        verified_cache.mkdir(parents=True)
        for entry in required_entries(lock):
            rel = Path(str(entry["path"]))
            dst = verified_cache / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_root / rel, dst)

    ok, cache_errors = validate_source(verified_cache, lock)
    if not ok:
        raise RuntimeError("verified LPC Terrains V7 cache failed:\n - " + "\n - ".join(cache_errors))

    install_verified_subset(verified_cache, destination, lock)
    write_provenance(lock, source_kind, source_value, destination)
    print(
        f"LPC Terrains V7 restored and verified: {destination.relative_to(ROOT)} "
        f"({len(required_entries(lock))} locked files)"
    )
    print(f"Attribution preserved: {destination / str(lock['attributionFile'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
