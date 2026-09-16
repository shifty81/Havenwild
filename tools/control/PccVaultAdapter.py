#!/usr/bin/env python3
"""Universal project-PCC adapter for a governed machine-wide Vault.

This module is deliberately project-agnostic. A project supplies a lock file with
exact required-file fingerprints plus optional Vault placement metadata. The
adapter may then verify, promote, hydrate, or report the dependency without
knowing game-specific semantics.

Resolution/promotion policy:
  1. valid project-local source
  2. valid shared Vault source
  3. valid project-local verified cache
  4. caller-owned explicit overrides / network acquisition

The caller remains responsible for transport-specific acquisition. Once a source
is verified, this adapter can promote it to the Vault transactionally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA = "pcc.universal_vault_contract.v1"
LOCK_SCHEMAS = {
    "havenwild.external_dependency_lock.v1",
    "pcc.external_dependency_lock.v1",
}
PROJECT_DEPENDENCY_SCHEMA = "pcc.vault_project_dependencies.v1"
ASSET_SCHEMA = "pcc.vault_asset.v1"
PROVENANCE_SCHEMA = "pcc.vault_provenance.v1"
_TRUE = {"1", "true", "yes", "on"}


class VaultError(RuntimeError):
    pass


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class VaultPaths:
    root: Path
    entry: Path
    source: Path
    archive_dir: Path
    metadata: Path
    licenses: Path


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def required_entries(lock: dict[str, Any]) -> list[dict[str, Any]]:
    entries = list((lock.get("verification") or {}).get("requiredFiles") or [])
    if not entries:
        raise VaultError("dependency lock contains no verification.requiredFiles entries")
    for entry in entries:
        if not entry.get("path") or not entry.get("sha256") or entry.get("bytes") is None:
            raise VaultError("dependency lock requiredFiles entries need path, bytes, and sha256")
    return entries


def validate_lock(lock: dict[str, Any]) -> None:
    if lock.get("schema") not in LOCK_SCHEMAS:
        raise VaultError(f"unsupported dependency lock schema: {lock.get('schema')!r}")
    if not str(lock.get("id") or "").strip():
        raise VaultError("dependency lock is missing id")
    required_entries(lock)


def validate_source(source: Path, lock: dict[str, Any]) -> VerificationResult:
    errors: list[str] = []
    for entry in required_entries(lock):
        rel = Path(str(entry["path"]))
        path = source / rel
        if not path.is_file():
            errors.append(f"missing {rel.as_posix()}")
            continue
        actual_size = path.stat().st_size
        expected_size = int(entry["bytes"])
        if actual_size != expected_size:
            errors.append(f"size mismatch {rel.as_posix()}: {actual_size} != {expected_size}")
            continue
        actual_hash = sha256(path)
        expected_hash = str(entry["sha256"]).lower()
        if actual_hash.lower() != expected_hash:
            errors.append(f"SHA-256 mismatch {rel.as_posix()}: {actual_hash} != {expected_hash}")
    return VerificationResult(not errors, tuple(errors))


def content_identity(lock: dict[str, Any]) -> str:
    rows = [
        f"{str(e['path']).replace('\\', '/')}|{int(e['bytes'])}|{str(e['sha256']).lower()}"
        for e in required_entries(lock)
    ]
    payload = "\n".join(sorted(rows)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def discover_vault_root(explicit: str | None = None) -> Path | None:
    values = [
        explicit,
        os.environ.get("PCC_VAULT_ROOT"),
        os.environ.get("FORGE_VAULT_ROOT"),
        os.environ.get("CORTEX_VAULT_ROOT"),
    ]
    for raw in values:
        if raw and str(raw).strip():
            return Path(str(raw).strip()).expanduser()
    if os.name == "nt":
        return Path(r"D:\Vault")
    return None


def vault_relative_path(lock: dict[str, Any]) -> Path | None:
    vault = lock.get("vault") or {}
    raw = str(vault.get("rootRelativePath") or "").strip().replace("\\", "/")
    if not raw:
        return None
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise VaultError(f"unsafe vault.rootRelativePath: {raw}")
    return path


def vault_paths(lock: dict[str, Any], vault_root: Path) -> VaultPaths:
    rel = vault_relative_path(lock)
    if rel is None:
        raise VaultError("dependency lock does not declare vault.rootRelativePath")
    entry = vault_root / rel
    return VaultPaths(
        root=vault_root,
        entry=entry,
        source=entry / "source",
        archive_dir=entry / "archive",
        metadata=entry / "metadata",
        licenses=entry / "licenses",
    )


def promotion_allowed(lock: dict[str, Any]) -> tuple[bool, str]:
    vault = lock.get("vault") or {}
    if not bool(vault.get("autoPromote", False)):
        return False, "autoPromote=false"
    labels = [str(x).strip() for x in (lock.get("licenseLabels") or []) if str(x).strip()]
    if not labels:
        return False, "licenseLabels missing"
    if not required_entries(lock):
        return False, "required file hashes missing"
    return True, "verified hashes + known license"


def _copy_verified_subset(source: Path, destination: Path, lock: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + f".staging-{os.getpid()}-{int(time.time())}")
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    try:
        for entry in required_entries(lock):
            rel = Path(str(entry["path"]))
            src = source / rel
            dst = staging / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        result = validate_source(staging, lock)
        if not result.ok:
            raise VaultError("staged verification failed: " + "; ".join(result.errors))
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _quarantine_entry(paths: VaultPaths, reason: str) -> Path:
    quarantine_root = paths.root / "Quarantine"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = paths.entry.name or "dependency"
    target = quarantine_root / f"{safe_name}-{stamp}"
    suffix = 1
    while target.exists():
        suffix += 1
        target = quarantine_root / f"{safe_name}-{stamp}-{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(paths.entry), str(target))
    (target / "QUARANTINE_REASON.txt").write_text(reason + "\n", encoding="utf-8")
    return target


def _write_metadata(paths: VaultPaths, lock: dict[str, Any], project_root: Path | None, source_kind: str) -> None:
    paths.metadata.mkdir(parents=True, exist_ok=True)
    paths.licenses.mkdir(parents=True, exist_ok=True)
    identity = content_identity(lock)
    asset = {
        "schema": ASSET_SCHEMA,
        "id": lock["id"],
        "displayName": lock.get("displayName") or lock["id"],
        "contentHash": identity,
        "verified": True,
        "verificationMode": (lock.get("verification") or {}).get("mode"),
        "licenseLabels": list(lock.get("licenseLabels") or []),
        "sourcePage": lock.get("sourcePage"),
        "sourceRelativePath": "source",
        "archiveRelativePath": "archive",
        "metadataRelativePath": "metadata",
        "requiredFileCount": len(required_entries(lock)),
    }
    provenance = {
        "schema": PROVENANCE_SCHEMA,
        "dependencyId": lock["id"],
        "contentHash": identity,
        "promotedUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sourceKind": source_kind,
        "sourceProject": str(project_root) if project_root else None,
        "sourcePage": lock.get("sourcePage"),
        "licenseLabels": list(lock.get("licenseLabels") or []),
    }
    (paths.entry / "asset.json").write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
    (paths.metadata / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    (paths.metadata / "source-lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    attribution = str(lock.get("attributionFile") or "").strip()
    if attribution:
        source_attribution = paths.source / attribution
        if source_attribution.is_file():
            shutil.copy2(source_attribution, paths.licenses / source_attribution.name)


def promote(source: Path, lock: dict[str, Any], vault_root: Path, project_root: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    validate_lock(lock)
    allowed, reason = promotion_allowed(lock)
    if not allowed and not force:
        return {"status": "REVIEW_REQUIRED", "reason": reason, "dependencyId": lock["id"]}
    result = validate_source(source, lock)
    if not result.ok:
        raise VaultError("source is not the locked dependency: " + "; ".join(result.errors))
    paths = vault_paths(lock, vault_root)
    existing = validate_source(paths.source, lock) if paths.source.exists() else VerificationResult(False, ("vault source missing",))
    if existing.ok:
        _write_metadata(paths, lock, project_root, "existing_verified_vault")
        return {"status": "ALREADY_PRESENT", "path": str(paths.source), "dependencyId": lock["id"], "contentHash": content_identity(lock)}
    if paths.entry.exists():
        quarantined = _quarantine_entry(paths, "Existing Vault entry failed exact lock verification before promotion.")
    else:
        quarantined = None
    paths.entry.mkdir(parents=True, exist_ok=True)
    _copy_verified_subset(source, paths.source, lock)
    _write_metadata(paths, lock, project_root, "verified_project_source")
    return {
        "status": "PROMOTED",
        "path": str(paths.source),
        "dependencyId": lock["id"],
        "contentHash": content_identity(lock),
        "quarantinedPrevious": str(quarantined) if quarantined else None,
    }


def hydrate(destination: Path, lock: dict[str, Any], vault_root: Path) -> dict[str, Any]:
    validate_lock(lock)
    paths = vault_paths(lock, vault_root)
    result = validate_source(paths.source, lock)
    if not result.ok:
        return {"status": "VAULT_MISS", "dependencyId": lock["id"], "errors": list(result.errors), "path": str(paths.source)}
    _copy_verified_subset(paths.source, destination, lock)
    return {"status": "HYDRATED", "dependencyId": lock["id"], "source": str(paths.source), "destination": str(destination)}


def archive_candidate(lock: dict[str, Any], vault_root: Path) -> Path | None:
    name = str(lock.get("archiveFileName") or "").strip()
    if not name:
        return None
    paths = vault_paths(lock, vault_root)
    candidate = paths.archive_dir / name
    return candidate if candidate.is_file() else None


def ensure_project_source(project_root: Path, lock_path: Path, vault_root: Path | None = None) -> dict[str, Any]:
    lock = _json(lock_path)
    validate_lock(lock)
    destination = project_root / str(lock.get("projectMount") or "")
    if not str(lock.get("projectMount") or "").strip():
        raise VaultError("dependency lock is missing projectMount")
    local = validate_source(destination, lock)
    root = vault_root or discover_vault_root()
    if local.ok:
        promoted = None
        if root is not None:
            try:
                promoted = promote(destination, lock, root, project_root)
            except (OSError, VaultError) as exc:
                promoted = {"status": "VAULT_PROMOTION_WARNING", "reason": str(exc)}
        return {"status": "PROJECT_READY", "destination": str(destination), "promotion": promoted}
    if root is not None:
        try:
            hydrated = hydrate(destination, lock, root)
            if hydrated.get("status") == "HYDRATED":
                return hydrated
        except (OSError, VaultError) as exc:
            return {"status": "VAULT_WARNING", "reason": str(exc), "destination": str(destination)}
    cache_raw = str(lock.get("cacheRoot") or "").strip()
    if cache_raw:
        verified_cache = project_root / cache_raw / "verified_source"
        cache_result = validate_source(verified_cache, lock)
        if cache_result.ok:
            _copy_verified_subset(verified_cache, destination, lock)
            promoted = None
            if root is not None:
                try:
                    promoted = promote(verified_cache, lock, root, project_root)
                except (OSError, VaultError) as exc:
                    promoted = {"status": "VAULT_PROMOTION_WARNING", "reason": str(exc)}
            return {"status": "CACHE_HYDRATED", "source": str(verified_cache), "destination": str(destination), "promotion": promoted}
    archive = archive_candidate(lock, root) if root is not None and vault_relative_path(lock) is not None else None
    return {
        "status": "MISS",
        "dependencyId": lock["id"],
        "destination": str(destination),
        "vaultRoot": str(root) if root else None,
        "vaultArchive": str(archive) if archive else None,
        "localErrors": list(local.errors),
    }


def project_dependency_manifest(project_root: Path) -> Path:
    return project_root / "content/architecture/pcc_vault_dependencies_v1.json"


def load_project_dependencies(project_root: Path) -> dict[str, Any]:
    path = project_dependency_manifest(project_root)
    if not path.is_file():
        return {"schema": PROJECT_DEPENDENCY_SCHEMA, "project": project_root.name, "dependencies": []}
    data = _json(path)
    if data.get("schema") != PROJECT_DEPENDENCY_SCHEMA:
        raise VaultError(f"unsupported project Vault dependency manifest schema: {data.get('schema')!r}")
    return data


def status(project_root: Path, vault_root: Path | None = None) -> dict[str, Any]:
    root = vault_root or discover_vault_root()
    manifest = load_project_dependencies(project_root)
    rows = []
    for item in manifest.get("dependencies") or []:
        rel = str(item.get("lock") or "").strip()
        if not rel:
            continue
        lock_path = project_root / rel
        if not lock_path.is_file():
            rows.append({"lock": rel, "status": "LOCK_MISSING"})
            continue
        lock = _json(lock_path)
        validate_lock(lock)
        project_mount = project_root / str(lock.get("projectMount") or "")
        local = validate_source(project_mount, lock)
        row: dict[str, Any] = {
            "id": lock["id"],
            "lock": rel,
            "projectReady": local.ok,
            "projectMount": str(project_mount),
            "vaultConfigured": vault_relative_path(lock) is not None,
            "promotionAllowed": promotion_allowed(lock)[0],
        }
        if root is not None and row["vaultConfigured"]:
            paths = vault_paths(lock, root)
            vault_result = validate_source(paths.source, lock)
            row["vaultReady"] = vault_result.ok
            row["vaultSource"] = str(paths.source)
            row["vaultArchive"] = str(archive_candidate(lock, root) or "")
        else:
            row["vaultReady"] = False
            row["vaultSource"] = None
        rows.append(row)
    return {
        "schema": "pcc.vault_status.v1",
        "project": manifest.get("project") or project_root.name,
        "vaultRoot": str(root) if root else None,
        "vaultAvailable": bool(root and root.exists()),
        "dependencyCount": len(rows),
        "dependencies": rows,
    }


def sync(project_root: Path, vault_root: Path | None = None) -> dict[str, Any]:
    root = vault_root or discover_vault_root()
    if root is None:
        raise VaultError("no Vault root configured; set PCC_VAULT_ROOT or FORGE_VAULT_ROOT")
    root.mkdir(parents=True, exist_ok=True)
    (root / "Assets").mkdir(parents=True, exist_ok=True)
    (root / "Dependencies").mkdir(parents=True, exist_ok=True)
    (root / "Quarantine").mkdir(parents=True, exist_ok=True)
    manifest = load_project_dependencies(project_root)
    results = []
    for item in manifest.get("dependencies") or []:
        rel = str(item.get("lock") or "").strip()
        if not rel:
            continue
        lock_path = project_root / rel
        if not lock_path.is_file():
            results.append({"lock": rel, "status": "LOCK_MISSING"})
            continue
        results.append({"lock": rel, **ensure_project_source(project_root, lock_path, root)})
    return {
        "schema": "pcc.vault_sync.v1",
        "project": manifest.get("project") or project_root.name,
        "vaultRoot": str(root),
        "results": results,
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pcc-vault-selftest-") as td:
        root = Path(td)
        project = root / "project"
        vault = root / "Vault"
        source = project / "local/source"
        source.mkdir(parents=True)
        payload = b"vault-contract-self-test\n"
        (source / "asset.bin").write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        lock = {
            "schema": "pcc.external_dependency_lock.v1",
            "id": "self_test_asset",
            "displayName": "Self Test Asset",
            "projectMount": "local/source",
            "cacheRoot": ".local/dependencies/self_test_asset",
            "licenseLabels": ["TEST-ONLY"],
            "verification": {"mode": "required_file_sha256", "requiredFiles": [{"path": "asset.bin", "bytes": len(payload), "sha256": digest}]},
            "vault": {"rootRelativePath": "Assets/Test/self-test-asset", "autoPromote": True},
        }
        lock_path = project / "lock.json"
        lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")
        first = ensure_project_source(project, lock_path, vault)
        shutil.rmtree(source)
        second = ensure_project_source(project, lock_path, vault)
        final = validate_source(source, lock)
        if first.get("status") != "PROJECT_READY" or second.get("status") != "HYDRATED" or not final.ok:
            raise VaultError(f"self-test failed: first={first} second={second} final={final}")
        return {"schema": "pcc.vault_self_test.v1", "status": "PASS", "promotion": first, "hydration": second}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status", "sync", "ensure", "promote", "hydrate", "self-test"])
    ap.add_argument("--root")
    ap.add_argument("--lock")
    ap.add_argument("--source")
    ap.add_argument("--destination")
    ap.add_argument("--vault-root")
    ap.add_argument("--pretty", action="store_true")
    ns = ap.parse_args()
    try:
        if ns.action == "self-test":
            payload = self_test()
        else:
            if not ns.root:
                raise VaultError("--root is required")
            project_root = Path(ns.root).resolve()
            vault_root = discover_vault_root(ns.vault_root)
            if ns.action == "status":
                payload = status(project_root, vault_root)
            elif ns.action == "sync":
                payload = sync(project_root, vault_root)
            else:
                if not ns.lock:
                    raise VaultError("--lock is required")
                lock_path = Path(ns.lock)
                if not lock_path.is_absolute():
                    lock_path = project_root / lock_path
                lock = _json(lock_path)
                validate_lock(lock)
                if vault_root is None:
                    raise VaultError("no Vault root configured")
                if ns.action == "ensure":
                    payload = ensure_project_source(project_root, lock_path, vault_root)
                elif ns.action == "promote":
                    if not ns.source:
                        raise VaultError("--source is required for promote")
                    payload = promote(Path(ns.source).resolve(), lock, vault_root, project_root)
                elif ns.action == "hydrate":
                    destination = Path(ns.destination).resolve() if ns.destination else project_root / str(lock["projectMount"])
                    payload = hydrate(destination, lock, vault_root)
                else:
                    raise AssertionError(ns.action)
        print(json.dumps(payload, indent=2 if ns.pretty else None))
        return 0
    except (OSError, ValueError, VaultError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": "pcc.vault_error.v1", "status": "FAIL", "error": str(exc)}, indent=2), file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
