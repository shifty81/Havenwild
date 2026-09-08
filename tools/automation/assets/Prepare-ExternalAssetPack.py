#!/usr/bin/env python3
"""Extract, inventory, and register a machine-local asset pack for Havenwild.

Raw files remain outside the repository. A compact project index is written into
content/assets/intake/external_pack_indexes so source-only rollups retain enough
metadata for Codex and the editor to understand the available library.
"""
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
from typing import Any

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - build doctor surfaces this clearly
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc

ROOT = Path(__file__).resolve().parents[3]
LOCAL_ROOTS = ROOT / ".local/havenwild_external_asset_roots.json"
PROJECT_INDEX_ROOT = ROOT / "content/assets/intake/external_pack_indexes"
IMAGE_EXTENSIONS = {".png", ".gif", ".jpg", ".jpeg", ".bmp", ".webp"}
GRID_CANDIDATES = (8, 16, 24, 32, 40, 48, 64, 72, 96, 128, 192)
LICENSE_CHOICES = {
    "cc0",
    "project_owned",
    "allowed_with_attribution",
    "unknown_requires_review",
    "blocked_reference_only",
}


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return value or "asset_pack"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if target != destination_resolved and destination_resolved not in target.parents:
                raise ValueError(f"unsafe archive entry escapes destination: {member.filename}")
        bundle.extractall(destination)


def classify(relative: Path) -> list[str]:
    text = relative.as_posix().lower()
    groups: list[str] = []
    keywords = {
        "terrain": "terrain",
        "tile": "tile",
        "grass": "terrain.grass",
        "water": "terrain.water",
        "shore": "terrain.coast",
        "coast": "terrain.coast",
        "sand": "terrain.coast",
        "cliff": "terrain.cliff",
        "cave": "environment.cave",
        "dungeon": "environment.dungeon",
        "house": "structure.building",
        "building": "structure.building",
        "castle": "structure.building",
        "roof": "structure.roof",
        "wall": "structure.wall",
        "door": "structure.door",
        "fence": "structure.fence",
        "bridge": "structure.bridge",
        "tree": "foliage.tree",
        "bush": "foliage.bush",
        "flower": "foliage.flower",
        "farm": "farming",
        "crop": "farming.crop",
        "animal": "character.animal",
        "chicken": "character.animal",
        "pig": "character.animal",
        "horse": "character.animal",
        "llama": "character.animal",
        "cat": "character.animal",
        "character": "character",
        "player": "character",
        "npc": "character",
        "walk": "animation.walk",
        "idle": "animation.idle",
        "eat": "animation.eat",
        "shadow": "animation.shadow",
        "icon": "ui.icon",
        "inventory": "ui.icon",
        "ui": "ui",
        "effect": "effect",
        "weapon": "equipment",
        "tool": "equipment",
        "armor": "equipment.armor",
        "clothing": "equipment.clothing",
        "hair": "character.hair",
        "interior": "environment.interior",
        "inside": "environment.interior",
        "furniture": "environment.furniture",
    }
    for key, group in keywords.items():
        if key in text and group not in groups:
            groups.append(group)
    return groups or ["unclassified"]


def inspect_image(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        width, height = image.size
        frame_count = int(getattr(image, "n_frames", 1))
        mode = image.mode
        grid_candidates = [
            size for size in GRID_CANDIDATES if width % size == 0 and height % size == 0
        ]
        return {
            "width": width,
            "height": height,
            "mode": mode,
            "frameCount": frame_count,
            "gridCandidates": grid_candidates,
            "likelySpriteSheet": bool(frame_count > 1 or width >= 64 or height >= 64),
            "likelyMultiTile": bool(width > 32 or height > 32),
        }


def load_roots() -> dict[str, Any]:
    if not LOCAL_ROOTS.is_file():
        return {"schema": "havenwild.external_asset_roots.local.v0_2", "roots": []}
    return json.loads(LOCAL_ROOTS.read_text(encoding="utf-8"))


def save_roots(payload: dict[str, Any]) -> None:
    LOCAL_ROOTS.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_ROOTS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def register_root(
    pack_id: str,
    display_name: str,
    raw_root: Path,
    license_status: str,
    attribution: str,
    source_url: str,
) -> None:
    payload = load_roots()
    roots = payload.setdefault("roots", [])
    record = {
        "id": pack_id,
        "displayName": display_name,
        "path": str(raw_root.resolve()).replace("\\", "/"),
        "enabled": True,
        "licenseStatus": license_status,
        "attribution": attribution,
        "sourceUrl": source_url,
        "notes": "Machine-local external source. Open in Pixel Studio and create a project working copy before editing or publishing.",
    }
    for index, existing in enumerate(roots):
        if existing.get("id") == pack_id:
            roots[index] = record
            break
    else:
        roots.append(record)
    save_roots(payload)


def inventory(raw_root: Path, pack_id: str, args: argparse.Namespace) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {"files": 0, "images": 0, "unreadableImages": 0}
    category_counts: dict[str, int] = {}
    for path in sorted(item for item in raw_root.rglob("*") if item.is_file()):
        relative = path.relative_to(raw_root)
        counts["files"] += 1
        record: dict[str, Any] = {
            "relativePath": relative.as_posix(),
            "extension": path.suffix.lower(),
            "sizeBytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "promotionState": "cataloged_source_only",
        }
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            counts["images"] += 1
            classes = classify(relative)
            record["classes"] = classes
            for category in classes:
                category_counts[category] = category_counts.get(category, 0) + 1
            try:
                record.update(inspect_image(path))
            except Exception as error:  # preserve the record for manual review
                counts["unreadableImages"] += 1
                record["imageError"] = str(error)
        records.append(record)
    return {
        "schema": "havenwild.external_asset_pack_index.v0_1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "pack": {
            "id": pack_id,
            "displayName": args.display_name,
            "archiveName": args.archive.name,
            "archiveSha256": sha256_file(args.archive),
            "externalRawRoot": str(raw_root.resolve()).replace("\\", "/"),
            "licenseStatus": args.license_status,
            "attribution": args.attribution,
            "sourceUrl": args.source_url,
            "rawFilesCommitted": False,
            "rawFilesPackaged": False,
        },
        "summary": {**counts, "categoryCounts": dict(sorted(category_counts.items()))},
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Path to Asset Pack.zip")
    parser.add_argument(
        "--library-root",
        type=Path,
        default=Path(os.environ.get("HAVENWILD_ASSET_LIBRARY", "~/HavenwildAssetLibrary")).expanduser(),
        help="External PC library root; defaults to ~/HavenwildAssetLibrary",
    )
    parser.add_argument("--pack-id", default="", help="Stable identifier; defaults to archive name")
    parser.add_argument("--display-name", default="Asset Pack")
    parser.add_argument(
        "--license-status",
        default="unknown_requires_review",
        choices=sorted(LICENSE_CHOICES),
    )
    parser.add_argument("--attribution", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--replace", action="store_true", help="Replace an existing extracted pack")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.archive = args.archive.expanduser().resolve()
    if not args.archive.is_file():
        print(f"ERROR: archive not found: {args.archive}", file=sys.stderr)
        return 2
    if not zipfile.is_zipfile(args.archive):
        print(f"ERROR: not a readable ZIP archive: {args.archive}", file=sys.stderr)
        return 2

    pack_id = slugify(args.pack_id or args.archive.stem)
    pack_root = args.library_root.expanduser().resolve() / "packs" / pack_id
    raw_root = pack_root / "raw"
    if raw_root.exists():
        if not args.replace:
            print(f"ERROR: pack already exists: {raw_root}\nUse --replace to rebuild it.", file=sys.stderr)
            return 2
        shutil.rmtree(pack_root)
    raw_root.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {args.archive} -> {raw_root}")
    safe_extract(args.archive, raw_root)
    index = inventory(raw_root, pack_id, args)

    local_catalog = pack_root / "catalog" / f"{pack_id}.json"
    local_catalog.parent.mkdir(parents=True, exist_ok=True)
    local_catalog.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    PROJECT_INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    project_index = PROJECT_INDEX_ROOT / f"{pack_id}.json"
    project_payload = json.loads(json.dumps(index))
    project_payload["pack"]["externalRawRoot"] = f"external://{pack_id}"
    project_index.write_text(json.dumps(project_payload, indent=2) + "\n", encoding="utf-8")
    register_root(
        pack_id,
        args.display_name,
        raw_root,
        args.license_status,
        args.attribution,
        args.source_url,
    )

    summary = index["summary"]
    print(f"Cataloged {summary['files']} files and {summary['images']} images")
    print(f"Local catalog: {local_catalog}")
    print(f"Project metadata index: {project_index}")
    print(f"Pixel Studio root registration: {LOCAL_ROOTS}")
    print("Raw files remain outside the repository and will not be packaged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
