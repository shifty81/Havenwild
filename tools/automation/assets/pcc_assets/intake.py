from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LICENSE_NAMES = (
    "license", "licence", "copying", "credits", "credit",
    "authors", "attribution", "readme",
)
MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga",
    ".tsx", ".tmx", ".json", ".xml", ".ron", ".toml", ".yaml", ".yml",
    ".ase", ".aseprite", ".kra", ".psd", ".wav", ".ogg", ".flac",
    ".glb", ".gltf", ".obj", ".fbx", ".blend",
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _kind(name: str) -> str:
    lower = name.lower()
    suffix = Path(lower).suffix
    basename = Path(lower).name
    if any(token in basename for token in LICENSE_NAMES):
        return "provenance_evidence"
    if suffix in {".tsx", ".tmx"}:
        return "tiled_metadata"
    if suffix == ".png":
        return "image_sheet_or_image"
    if suffix in MEDIA_EXTENSIONS:
        return "asset_or_metadata"
    return "other"


def _read_text_evidence(path: Path, max_chars: int = 4096) -> str | None:
    if not any(token in path.name.lower() for token in LICENSE_NAMES):
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return None


def build_source_manifest(source: Path, source_id: str | None = None) -> dict[str, Any]:
    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    records: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    container_type: str

    if source.is_dir():
        container_type = "directory"
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = path.relative_to(source).as_posix()
            record = {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
                "kind": _kind(rel),
            }
            records.append(record)
            snippet = _read_text_evidence(path)
            if snippet is not None:
                provenance.append({
                    "path": rel,
                    "sha256": record["sha256"],
                    "snippet": snippet,
                })
    elif source.suffix.lower() == ".zip":
        container_type = "zip"
        with zipfile.ZipFile(source) as zf:
            for info in sorted(zf.infolist(), key=lambda i: i.filename.lower()):
                if info.is_dir():
                    continue
                normalized = info.filename.replace("\\", "/").lstrip("/")
                parts = Path(normalized).parts
                if normalized.startswith("../") or ".." in parts:
                    raise ValueError(f"unsafe ZIP entry: {info.filename}")
                data = zf.read(info)
                record = {
                    "path": normalized,
                    "bytes": len(data),
                    "sha256": _sha256_bytes(data),
                    "kind": _kind(normalized),
                }
                records.append(record)
                if any(token in Path(normalized).name.lower() for token in LICENSE_NAMES):
                    provenance.append({
                        "path": normalized,
                        "sha256": record["sha256"],
                        "snippet": data[:4096].decode("utf-8", errors="replace"),
                    })
    else:
        container_type = "file"
        record = {
            "path": source.name,
            "bytes": source.stat().st_size,
            "sha256": _sha256_file(source),
            "kind": _kind(source.name),
        }
        records.append(record)
        snippet = _read_text_evidence(source)
        if snippet is not None:
            provenance.append({
                "path": source.name,
                "sha256": record["sha256"],
                "snippet": snippet,
            })

    by_kind: dict[str, int] = {}
    for record in records:
        by_kind[record["kind"]] = by_kind.get(record["kind"], 0) + 1

    return {
        "schema": "pcc.asset.source_manifest.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceId": source_id or source.stem,
        "sourcePath": source.as_posix(),
        "containerType": container_type,
        "containerSha256": _sha256_file(source) if source.is_file() else None,
        "summary": {
            "fileCount": len(records),
            "bytes": sum(int(r["bytes"]) for r in records),
            "byKind": dict(sorted(by_kind.items())),
            "provenanceEvidenceCount": len(provenance),
        },
        "files": records,
        "provenanceEvidence": provenance,
        "policy": {
            "sourceBytesModified": False,
            "archiveExtracted": False,
            "runtimePromotionPerformed": False,
        },
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
