from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class AssetCache:
    """Persistent content/hash cache for large asset libraries.

    SQLite is deliberately used here instead of one giant JSON cache:
    - updates are incremental/atomic;
    - interrupted scans preserve completed work;
    - lookups stay fast with tens of thousands of source files.
    """

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS file_hash (
                physical_path TEXT PRIMARY KEY,
                size_bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                sha256 TEXT NOT NULL
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis (
                sha256 TEXT NOT NULL,
                analysis_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (sha256, analysis_key)
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                physical_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                inventory_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (physical_path, size_bytes, mtime_ns, inventory_key)
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_file (
                source_root TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                domain TEXT,
                analyzer_route TEXT,
                variant_family TEXT,
                deep_state TEXT,
                bytes INTEGER,
                width INTEGER,
                height INTEGER,
                logical_path TEXT,
                physical_path TEXT,
                PRIMARY KEY (source_root, relative_path)
            )
            """
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_file_sha ON catalog_file(sha256)"
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_file_domain ON catalog_file(domain)"
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_file_family ON catalog_file(variant_family)"
        )
        self.db.execute(
            "INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)",
            (str(SCHEMA_VERSION),),
        )
        self.db.commit()

    def close(self) -> None:
        self.db.commit()
        self.db.close()

    def get_file_hash(self, physical_path: str, size: int, mtime_ns: int) -> str | None:
        row = self.db.execute(
            """
            SELECT sha256 FROM file_hash
            WHERE physical_path=? AND size_bytes=? AND mtime_ns=?
            """,
            (physical_path, int(size), int(mtime_ns)),
        ).fetchone()
        return row[0] if row else None

    def put_file_hash(
        self, physical_path: str, size: int, mtime_ns: int, sha256: str
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO file_hash
            (physical_path,size_bytes,mtime_ns,sha256) VALUES(?,?,?,?)
            """,
            (physical_path, int(size), int(mtime_ns), sha256),
        )

    def get_analysis(self, sha256: str, analysis_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            """
            SELECT payload_json FROM analysis
            WHERE sha256=? AND analysis_key=?
            """,
            (sha256, analysis_key),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put_analysis(
        self, sha256: str, analysis_key: str, payload: dict[str, Any]
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO analysis
            (sha256,analysis_key,payload_json) VALUES(?,?,?)
            """,
            (sha256, analysis_key, json.dumps(payload, separators=(",", ":"))),
        )

    def get_inventory(
        self,
        physical_path: str,
        size: int,
        mtime_ns: int,
        inventory_key: str,
    ) -> dict[str, Any] | None:
        row = self.db.execute(
            """
            SELECT payload_json FROM inventory
            WHERE physical_path=? AND size_bytes=? AND mtime_ns=? AND inventory_key=?
            """,
            (physical_path, int(size), int(mtime_ns), inventory_key),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put_inventory(
        self,
        physical_path: str,
        size: int,
        mtime_ns: int,
        inventory_key: str,
        payload: dict[str, Any],
    ) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO inventory
            (physical_path,size_bytes,mtime_ns,inventory_key,payload_json)
            VALUES(?,?,?,?,?)
            """,
            (
                physical_path,
                int(size),
                int(mtime_ns),
                inventory_key,
                json.dumps(payload, separators=(",", ":")),
            ),
        )

    def replace_catalog_files(
        self,
        source_root: str,
        records: list[dict[str, Any]],
    ) -> None:
        self.db.execute(
            "DELETE FROM catalog_file WHERE source_root=?",
            (source_root,),
        )
        rows = [
            (
                source_root,
                record["relativePath"],
                record["sha256"],
                record.get("domain"),
                record.get("analyzerRoute"),
                record.get("variantFamily"),
                record.get("deepAnalysisState"),
                int(record.get("bytes") or 0),
                record.get("width"),
                record.get("height"),
                record.get("logicalPath"),
                record.get("physicalPath"),
            )
            for record in records
        ]
        self.db.executemany(
            """
            INSERT INTO catalog_file(
                source_root,relative_path,sha256,domain,analyzer_route,
                variant_family,deep_state,bytes,width,height,logical_path,physical_path
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )

    def stats(self) -> dict[str, int]:
        def count(table: str) -> int:
            return int(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return {
            "fileHashCount": count("file_hash"),
            "inventoryCount": count("inventory"),
            "analysisCount": count("analysis"),
            "catalogFileCount": count("catalog_file"),
        }

    def commit(self) -> None:
        self.db.commit()


def hash_records(
    records: list[dict[str, Any]],
    cache: AssetCache,
    workers: int,
    progress: Callable[[str, int, int, Path], None] | None = None,
) -> dict[str, int]:
    """Populate record['sha256'] with cache-aware parallel hashing."""

    missing: list[tuple[int, Path, int, int]] = []
    hits = 0
    for index, record in enumerate(records):
        path = Path(record["physicalPath"])
        cached = cache.get_file_hash(
            str(path), int(record["bytes"]), int(record["mtimeNs"])
        )
        if cached:
            record["sha256"] = cached
            hits += 1
        else:
            missing.append(
                (index, path, int(record["bytes"]), int(record["mtimeNs"]))
            )

    total = len(records)
    completed = hits
    if progress and hits:
        progress("hash", completed, total, Path(f"{hits} cached"))

    worker_count = max(1, int(workers))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(sha256_file, path): (index, path, size, mtime_ns)
            for index, path, size, mtime_ns in missing
        }
        since_commit = 0
        for future in as_completed(futures):
            index, path, size, mtime_ns = futures[future]
            digest = future.result()
            records[index]["sha256"] = digest
            cache.put_file_hash(str(path), size, mtime_ns, digest)
            completed += 1
            since_commit += 1
            if since_commit >= 250:
                cache.commit()
                since_commit = 0
            if progress and (
                completed == total or completed % 250 == 0
            ):
                progress("hash", completed, total, path)

    cache.commit()
    return {
        "fileCount": total,
        "cacheHits": hits,
        "hashedNow": len(missing),
    }

from pathlib import Path
from typing import Any

CLASSIFIER_VERSION = "pcc-classify-v2"


REFERENCE_TOKENS = (
    "_ guides", "guides & palettes", "_ palette", "palette",
    "_ test scenes", "test scene", "demo", "example", "reference",
    "credits", "license", "licence", "readme",
)
TERRAIN_TOKENS = (
    "terrain", "cliff", "coast", "shore", "water", "grass", "dirt",
    "sand", "snow", "road", "path", "river", "pond", "ground",
    "mountain", "rock", "tile",
)
STRUCTURE_TOKENS = (
    "building", "structure", "house", "roof", "wall", "door", "window",
    "interior", "exterior", "fence", "bridge", "stairs", "ladder",
    "cave", "tavern", "shop", "barn", "shed",
)
CHARACTER_TOKENS = (
    "characters", "character", "body", "wardrobe", "hair", "beard",
    "head", "eyes", "clothes", "armor", "armour", "combat", "emotes",
)
UI_TOKENS = (
    "ui", "gui", "interface", "hud", "cursor", "button", "font",
)
ANIMATION_TOKENS = (
    "idle", "walk", "run", "jump", "climb", "slash", "thrust",
    "shoot", "spell", "hurt", "death", "sitting", "emotes",
)
VARIANT_CONTAINER_TOKENS = (
    "alternate", "variants", "variant", "colors", "colours",
    "skins", "palettes",
)
SEASONS = {"spring", "summer", "autumn", "fall", "winter"}
COLOR_WORDS = {
    "amber", "apple", "azure", "blue", "cerise", "charcoal", "coral",
    "cyan", "dove", "fern", "garnet", "green", "ice", "lavender",
    "lemon", "midnight", "mustard", "neptune", "ochre", "orange",
    "periwinkle", "plum", "purple", "red", "rose", "teal", "violet",
    "white", "yellow", "black", "brown", "gray", "grey",
}


def quick_png_dimensions(path: Path) -> tuple[int | None, int | None]:
    """Read PNG IHDR dimensions without decoding image pixels."""
    try:
        with path.open("rb") as fh:
            header = fh.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return None, None
        if header[12:16] != b"IHDR":
            return None, None
        return (
            int.from_bytes(header[16:20], "big"),
            int.from_bytes(header[20:24], "big"),
        )
    except OSError:
        return None, None


def classify_asset_path(
    relative_path: str,
    width: int | None = None,
    height: int | None = None,
    cell_width: int = 32,
    cell_height: int = 32,
) -> dict[str, Any]:
    lower = relative_path.replace("\\", "/").lower()
    name = Path(lower).name

    if any(token in lower for token in REFERENCE_TOKENS):
        domain = "reference"
    elif any(token in lower for token in CHARACTER_TOKENS):
        domain = "character"
    elif any(token in lower for token in STRUCTURE_TOKENS):
        domain = "structure"
    elif any(token in lower for token in TERRAIN_TOKENS):
        domain = "terrain"
    elif any(token in lower for token in UI_TOKENS):
        domain = "ui"
    elif any(token in name for token in ANIMATION_TOKENS):
        domain = "animation"
    else:
        domain = "prop"

    grid_compatible = bool(
        width and height
        and width % cell_width == 0
        and height % cell_height == 0
    )
    cells = (
        (width // cell_width) * (height // cell_height)
        if grid_compatible else None
    )

    if domain == "reference":
        route = "index_only"
    elif domain == "character":
        route = "character_family"
    elif domain == "ui":
        route = "index_only"
    elif not grid_compatible:
        route = "index_only"
    else:
        route = "sheet_deep"

    return {
        "domain": domain,
        "analyzerRoute": route,
        "gridCompatible": grid_compatible,
        "gridCellCount": cells,
    }


def variant_family_key(relative_path: str) -> str:
    """Normalize common variant/color/season paths into one family key."""
    parts = list(Path(relative_path.replace("\\", "/")).parts)
    lowered = [p.lower() for p in parts]

    # Generic "Alternate Colors/<variant>/Action.png" style.
    for i, part in enumerate(lowered[:-1]):
        if any(token in part for token in VARIANT_CONTAINER_TOKENS):
            if i + 1 < len(parts) - 1:
                parts[i + 1] = "{variant}"
            break

    # Seasonal source layouts often vary only by one folder or filename token.
    for i, part in enumerate(list(parts)):
        stem = Path(part).stem
        suffix = Path(part).suffix
        low = stem.lower()
        if low in SEASONS or low in COLOR_WORDS:
            parts[i] = "{variant}" + suffix
            continue
        for token in SEASONS:
            if token in low:
                parts[i] = stem.lower().replace(token, "{season}") + suffix
                break

    return "/".join(parts).lower()

import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import ProjectAdapter
from .sheet import analyze_sheet
from .tiled import inspect_tiled


PROFILE_NAMES = (
    "smart", "index", "terrain", "structures",
    "characters", "props", "animations", "full",
)
ANALYZER_VERSION = "pcc-sheet-v1"
DEFAULT_SMART_MAX_DEEP = 2500


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _write_checkpoint(
    path: Path | None,
    *,
    status: str,
    phase: str,
    completed: int,
    total: int,
    extra: dict[str, Any] | None = None,
) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "pcc.asset.scan_checkpoint.v1",
        "updatedUtc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "phase": phase,
        "completed": int(completed),
        "total": int(total),
        "remaining": max(0, int(total) - int(completed)),
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _profile_allows(record: dict[str, Any], profile: str) -> bool:
    if profile == "index":
        return False
    if not record.get("gridCompatible"):
        return False
    domain = record.get("domain")
    if profile == "full":
        return domain != "reference"
    if profile == "terrain":
        return domain == "terrain"
    if profile == "structures":
        return domain in {"structure", "prop"}
    if profile == "characters":
        return domain == "character"
    if profile == "props":
        return domain == "prop"
    if profile == "animations":
        return domain in {"animation", "character"}
    # smart
    return domain in {"terrain", "structure", "prop"}


def _candidate_rank(record: dict[str, Any], metadata_linked: bool) -> tuple:
    domain_rank = {
        "terrain": 0,
        "structure": 1,
        "prop": 2,
        "animation": 3,
        "character": 4,
        "ui": 8,
        "reference": 9,
    }.get(record.get("domain"), 7)
    cells = record.get("gridCellCount")
    return (
        0 if metadata_linked else 1,
        domain_rank,
        int(cells) if isinstance(cells, int) else 10**9,
        record.get("relativePath", ""),
    )


def _analysis_cache_key(
    adapter: ProjectAdapter,
    cell_width: int,
    cell_height: int,
    metadata_evidence: list[dict[str, Any]],
) -> str:
    digest = hashlib.sha256(
        json.dumps(metadata_evidence, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return (
        f"{ANALYZER_VERSION}:{adapter.name}:"
        f"{cell_width}x{cell_height}:{digest}"
    )


def _analyze_worker(
    physical_path: str,
    adapter: ProjectAdapter,
    cell_width: int,
    cell_height: int,
    metadata_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    return analyze_sheet(
        Path(physical_path),
        adapter,
        cell_width=cell_width,
        cell_height=cell_height,
        metadata_evidence=metadata_evidence,
    ).to_dict()


def scan_asset_root(
    root: Path,
    adapter: ProjectAdapter,
    cell_width: int | None = None,
    cell_height: int | None = None,
    max_files: int | None = None,
    progress=None,
    *,
    profile: str = "smart",
    workers: int | None = None,
    max_deep: int | None = None,
    cache_path: Path | None = None,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    if profile not in PROFILE_NAMES:
        raise ValueError(f"unknown scan profile: {profile}")

    requested = Path(root)
    logical_root = requested.absolute()
    physical_root = requested.resolve()
    if not physical_root.is_dir():
        raise FileNotFoundError(physical_root)

    cw = int(cell_width or adapter.default_cell_width)
    ch = int(cell_height or adapter.default_cell_height)
    worker_count = max(1, int(workers or min(8, os.cpu_count() or 4)))

    cache_path = cache_path or (
        Path("artifacts/asset-intake/cache/pcc_asset_cache.sqlite").absolute()
    )
    cache = AssetCache(cache_path)

    started = time.perf_counter()
    errors: list[dict[str, Any]] = []

    try:
        all_files = sorted(p for p in physical_root.rglob("*") if p.is_file())
        if max_files is not None:
            all_files = all_files[:max_files]

        png_paths = [p for p in all_files if p.suffix.lower() == ".png"]
        metadata_paths = [
            p for p in all_files if p.suffix.lower() in {".tsx", ".tmx"}
        ]

        inventory: list[dict[str, Any]] = []
        inventory_cache_hits = 0
        total_png = len(png_paths)
        for idx, path in enumerate(png_paths, 1):
            try:
                stat = path.stat()
                rel = _rel(physical_root, path)
                inventory_key = f"{CLASSIFIER_VERSION}:{cw}x{ch}:{rel.lower()}"
                cached_inventory = cache.get_inventory(
                    path.as_posix(),
                    stat.st_size,
                    stat.st_mtime_ns,
                    inventory_key,
                )
                if cached_inventory is not None:
                    inventory_cache_hits += 1
                    cached_inventory.update({
                        "relativePath": rel,
                        "logicalPath": (logical_root / rel).as_posix(),
                        "physicalPath": path.as_posix(),
                        "bytes": stat.st_size,
                        "mtimeNs": stat.st_mtime_ns,
                    })
                    inventory.append(cached_inventory)
                else:
                    width, height = quick_png_dimensions(path)
                    cls = classify_asset_path(rel, width, height, cw, ch)
                    record = {
                        "relativePath": rel,
                        "logicalPath": (logical_root / rel).as_posix(),
                        "physicalPath": path.as_posix(),
                        "bytes": stat.st_size,
                        "mtimeNs": stat.st_mtime_ns,
                        "width": width,
                        "height": height,
                        "variantFamily": variant_family_key(rel),
                        **cls,
                    }
                    cache.put_inventory(
                        path.as_posix(),
                        stat.st_size,
                        stat.st_mtime_ns,
                        inventory_key,
                        {
                            "width": width,
                            "height": height,
                            "variantFamily": record["variantFamily"],
                            "domain": record["domain"],
                            "analyzerRoute": record["analyzerRoute"],
                            "gridCompatible": record["gridCompatible"],
                            "gridCellCount": record["gridCellCount"],
                        },
                    )
                    inventory.append(record)
            except Exception as exc:
                errors.append({"path": _rel(physical_root, path), "error": str(exc)})
            if progress and (idx == 1 or idx % 1000 == 0 or idx == total_png):
                progress("inventory", idx, total_png, path)
        cache.commit()

        _write_checkpoint(
            checkpoint_path,
            status="RUNNING",
            phase="hash",
            completed=0,
            total=len(inventory),
            extra={"profile": profile},
        )
        hash_stats = hash_records(
            inventory, cache, worker_count, progress=progress
        )

        exact_groups: dict[str, list[str]] = defaultdict(list)
        variant_groups: dict[str, list[str]] = defaultdict(list)
        for record in inventory:
            exact_groups[record["sha256"]].append(record["relativePath"])
            variant_groups[record["variantFamily"]].append(record["relativePath"])

        exact_duplicate_groups = {
            digest: paths for digest, paths in exact_groups.items()
            if len(paths) > 1
        }
        structural_variant_groups = {
            key: paths for key, paths in variant_groups.items()
            if len(paths) > 1
        }

        # Metadata parsing is relatively cheap and is valuable evidence for
        # deciding which PNGs deserve deep analysis.
        tiled_by_image_name: dict[str, list[dict[str, Any]]] = {}
        tiled_records = []
        for idx, path in enumerate(metadata_paths, 1):
            if progress and (
                idx == 1 or idx % 100 == 0 or idx == len(metadata_paths)
            ):
                progress("metadata", idx, len(metadata_paths), path)
            try:
                ev = inspect_tiled(path)
                ev["relativePath"] = _rel(physical_root, path)
                tiled_records.append(ev)
                if path.suffix.lower() == ".tsx":
                    image_source = (ev.get("image") or {}).get("source")
                    if image_source:
                        tiled_by_image_name.setdefault(
                            Path(image_source).name.lower(), []
                        ).append(ev)
            except Exception as exc:
                errors.append({
                    "path": _rel(physical_root, path),
                    "error": str(exc),
                })

        # One deep analysis per unique content hash. Character variant families
        # are additionally reduced to one representative for smart/character
        # scans so alternate palette trees do not explode scan cost.
        seen_hashes: set[str] = set()
        seen_character_families: set[str] = set()
        deep_candidates: list[dict[str, Any]] = []
        deferred: list[dict[str, Any]] = []

        for record in inventory:
            allowed = _profile_allows(record, profile)
            if not allowed:
                record["deepAnalysisState"] = "indexed_only"
                continue

            digest = record["sha256"]
            if digest in seen_hashes:
                record["deepAnalysisState"] = "exact_duplicate_reuses_authority"
                continue

            if (
                record.get("domain") == "character"
                and profile in {"smart", "characters", "animations"}
            ):
                family = record["variantFamily"]
                if family in seen_character_families:
                    record["deepAnalysisState"] = "variant_family_deferred"
                    continue
                seen_character_families.add(family)

            seen_hashes.add(digest)
            metadata_linked = bool(
                tiled_by_image_name.get(Path(record["relativePath"]).name.lower())
            )
            record["_metadataLinked"] = metadata_linked
            deep_candidates.append(record)

        deep_candidates.sort(
            key=lambda r: _candidate_rank(r, bool(r.get("_metadataLinked")))
        )

        effective_max_deep = max_deep
        if effective_max_deep is None and profile == "smart":
            effective_max_deep = DEFAULT_SMART_MAX_DEEP
        if effective_max_deep is not None and len(deep_candidates) > effective_max_deep:
            overflow = deep_candidates[int(effective_max_deep):]
            deep_candidates = deep_candidates[:int(effective_max_deep)]
            for record in overflow:
                record["deepAnalysisState"] = "deferred_by_profile_budget"
                deferred.append({
                    "relativePath": record["relativePath"],
                    "sha256": record["sha256"],
                    "domain": record["domain"],
                    "reason": "deep analysis budget",
                })

        _write_checkpoint(
            checkpoint_path,
            status="RUNNING",
            phase="deep_analysis",
            completed=0,
            total=len(deep_candidates),
            extra={
                "profile": profile,
                "cachePath": cache_path.as_posix(),
                "deferredByBudget": len(deferred),
            },
        )

        sheets: list[dict[str, Any]] = []
        cache_hits_analysis = 0
        pending: list[tuple[dict[str, Any], list[dict[str, Any]], str]] = []

        for record in deep_candidates:
            metadata = tiled_by_image_name.get(
                Path(record["relativePath"]).name.lower(), []
            )
            metadata_evidence = [
                {
                    "kind": "tiled_tileset",
                    "path": x["relativePath"],
                    "summary": x["summary"],
                    "certification": x["certification"],
                }
                for x in metadata
            ]
            key = _analysis_cache_key(adapter, cw, ch, metadata_evidence)
            cached = cache.get_analysis(record["sha256"], key)
            if cached is not None:
                cache_hits_analysis += 1
                analysis = cached
                analysis["source"]["relativePath"] = record["relativePath"]
                analysis["source"]["logicalPath"] = record["logicalPath"]
                analysis["source"]["physicalPath"] = record["physicalPath"]
                analysis["source"]["sha256"] = record["sha256"]
                analysis["scanClassification"] = {
                    "domain": record["domain"],
                    "variantFamily": record["variantFamily"],
                    "profile": profile,
                    "cacheHit": True,
                }
                record["deepAnalysisState"] = "cache_hit"
                sheets.append(analysis)
            else:
                pending.append((record, metadata_evidence, key))

        completed = cache_hits_analysis
        if progress and completed:
            progress(
                "analyze", completed, len(deep_candidates),
                Path(f"{completed} cached analyses")
            )

        # Thread pool keeps Windows invocation straightforward and still helps
        # substantially with PNG read/zlib work. A later worker backend can
        # switch CPU-heavy analyzers to processes without changing this API.
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {
                pool.submit(
                    _analyze_worker,
                    record["physicalPath"],
                    adapter,
                    cw,
                    ch,
                    metadata_evidence,
                ): (record, key)
                for record, metadata_evidence, key in pending
            }

            since_commit = 0
            for future in as_completed(futures):
                record, key = futures[future]
                try:
                    analysis = future.result()
                    analysis["source"]["relativePath"] = record["relativePath"]
                    analysis["source"]["logicalPath"] = record["logicalPath"]
                    analysis["source"]["physicalPath"] = record["physicalPath"]
                    analysis["source"]["sha256"] = record["sha256"]
                    analysis["scanClassification"] = {
                        "domain": record["domain"],
                        "variantFamily": record["variantFamily"],
                        "profile": profile,
                        "cacheHit": False,
                    }
                    cache.put_analysis(record["sha256"], key, analysis)
                    record["deepAnalysisState"] = "analyzed"
                    sheets.append(analysis)
                    since_commit += 1
                    if since_commit >= 25:
                        cache.commit()
                        since_commit = 0
                except Exception as exc:
                    record["deepAnalysisState"] = "analysis_error"
                    errors.append({
                        "path": record["relativePath"],
                        "error": str(exc),
                    })

                completed += 1
                if progress and (
                    completed == len(deep_candidates)
                    or completed % 10 == 0
                ):
                    progress(
                        "analyze", completed, len(deep_candidates),
                        Path(record["relativePath"])
                    )
                if completed % 25 == 0 or completed == len(deep_candidates):
                    _write_checkpoint(
                        checkpoint_path,
                        status="RUNNING",
                        phase="deep_analysis",
                        completed=completed,
                        total=len(deep_candidates),
                        extra={
                            "profile": profile,
                            "analysisCacheHits": cache_hits_analysis,
                        },
                    )

        cache.commit()

        sheets.sort(
            key=lambda s: s.get("source", {}).get("relativePath", "")
        )

        assemblies = []
        for sheet in sheets:
            source_rel = sheet["source"]["relativePath"]
            for asm in sheet["assemblies"]:
                assemblies.append({
                    "assetId": f"{source_rel}#{asm['assembly_id']}",
                    "source": source_rel,
                    **asm,
                })

        cache.replace_catalog_files(physical_root.as_posix(), inventory)
        cache.commit()
        cache_stats = cache.stats()

        domain_counts = Counter(r["domain"] for r in inventory)
        route_counts = Counter(r["analyzerRoute"] for r in inventory)
        deep_state_counts = Counter(
            r.get("deepAnalysisState", "unassigned") for r in inventory
        )

        elapsed = time.perf_counter() - started
        catalog = {
            "schema": "pcc.asset.catalog.v2",
            "generatedUtc": datetime.now(timezone.utc).isoformat(),
            "rootIdentity": {
                "requestedPath": str(root),
                "logicalRoot": logical_root.as_posix(),
                "physicalRoot": physical_root.as_posix(),
                "logicalAndPhysicalDiffer": (
                    logical_root.as_posix().lower()
                    != physical_root.as_posix().lower()
                ),
            },
            "adapter": adapter.name,
            "scan": {
                "profile": profile,
                "workers": worker_count,
                "cellSize": [cw, ch],
                "maxFiles": max_files,
                "maxDeep": effective_max_deep,
                "elapsedSeconds": round(elapsed, 3),
                "cachePath": cache_path.as_posix(),
                "checkpointPath": (
                    checkpoint_path.as_posix() if checkpoint_path else None
                ),
                "detailStore": cache_path.as_posix(),
            },
            "policy": {
                "automaticRuntimeCertification": False,
                "semanticsInferredFromPixels": False,
                "sourcePixelsAreImmutableAuthority": True,
                "fullDeepScanIsExplicit": True,
                "smartScanDefault": True,
            },
            "summary": {
                "discoveredFileCount": len(all_files),
                "pngFileCount": len(inventory),
                "pngSheetCount": len(sheets),
                "tiledMetadataCount": len(tiled_records),
                "assemblyCandidateCount": len(assemblies),
                "exactDuplicateGroupCount": len(exact_duplicate_groups),
                "structuralVariantFamilyCount": len(structural_variant_groups),
                "deepCandidateCount": len(deep_candidates),
                "deepDeferredCount": len(deferred),
                "analysisCacheHits": cache_hits_analysis,
                "inventoryCacheHits": inventory_cache_hits,
                "hashCacheHits": hash_stats["cacheHits"],
                "hashedNow": hash_stats["hashedNow"],
                "errorCount": len(errors),
                "detailStoreCounts": cache_stats,
                "byDomain": dict(sorted(domain_counts.items())),
                "byAnalyzerRoute": dict(sorted(route_counts.items())),
                "byDeepAnalysisState": dict(sorted(deep_state_counts.items())),
            },
            "files": inventory,
            "sheets": sheets,
            "tiled": tiled_records,
            "assemblyIndex": assemblies,
            "exactDuplicateGroups": exact_duplicate_groups,
            "structuralVariantFamilies": structural_variant_groups,
            "deferred": deferred,
            "errors": errors,
        }

        _write_checkpoint(
            checkpoint_path,
            status="PASS" if not errors else "PASS_WITH_ERRORS",
            phase="complete",
            completed=len(deep_candidates),
            total=len(deep_candidates),
            extra={
                "profile": profile,
                "elapsedSeconds": round(elapsed, 3),
                "errorCount": len(errors),
            },
        )
        return catalog

    except KeyboardInterrupt:
        _write_checkpoint(
            checkpoint_path,
            status="INTERRUPTED",
            phase="interrupted",
            completed=0,
            total=0,
            extra={
                "profile": profile,
                "cachePath": cache_path.as_posix(),
                "message": "Completed hash/analysis cache entries are preserved.",
            },
        )
        raise
    finally:
        cache.close()


def compact_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Return the normal operational catalog.

    File-level records and full sheet analyses remain authoritative in SQLite.
    This JSON retains scan/source identity, summaries, sheet references and the
    multi-tile assembly index needed by downstream review/prefab tooling.
    """
    sheets = []
    for sheet in catalog.get("sheets", []):
        source = sheet.get("source", {})
        sheets.append({
            "source": {
                "relativePath": source.get("relativePath"),
                "logicalPath": source.get("logicalPath"),
                "sha256": source.get("sha256"),
                "bytes": source.get("bytes"),
                "width": source.get("width"),
                "height": source.get("height"),
            },
            "grid": sheet.get("grid"),
            "classification": sheet.get("scanClassification"),
            "assemblyCount": len(sheet.get("assemblies", [])),
            "animationCount": len(sheet.get("animations", [])),
            "warningCount": len(sheet.get("warnings", [])),
        })

    return {
        "schema": catalog.get("schema", "pcc.asset.catalog.v2"),
        "generatedUtc": catalog.get("generatedUtc"),
        "rootIdentity": catalog.get("rootIdentity"),
        "adapter": catalog.get("adapter"),
        "scan": catalog.get("scan"),
        "storage": {
            "mode": "compact",
            "detailStore": catalog.get("scan", {}).get("detailStore"),
            "fileRecordsInSqlite": True,
            "analysisPayloadsInSqlite": True,
            "exactDuplicateMembershipInSqlite": True,
            "structuralVariantMembershipInSqlite": True,
        },
        "policy": catalog.get("policy"),
        "summary": catalog.get("summary"),
        "sheets": sheets,
        "tiled": catalog.get("tiled", []),
        "assemblyIndex": catalog.get("assemblyIndex", []),
        "deferred": catalog.get("deferred", []),
        "errors": catalog.get("errors", []),
    }


def write_catalog(
    path: Path,
    catalog: dict[str, Any],
    *,
    detail: str = "compact",
) -> None:
    if detail not in {"compact", "full"}:
        raise ValueError(f"unknown catalog detail: {detail}")
    payload = catalog if detail == "full" else compact_catalog(catalog)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Never expose a partially-written or syntactically-invalid authoritative
    # catalog.  The previous compact writer accidentally appended the literal
    # characters ``\\n`` after the JSON document; json.loads correctly
    # rejected that as trailing data.  Serialize once, round-trip it, write a
    # sibling temporary file, verify the exact bytes, then atomically replace.
    serialized = json.dumps(payload, indent=2) + "\n"
    decoded = json.loads(serialized)
    if not isinstance(decoded, dict):
        raise ValueError("asset catalog root must be a JSON object")

    from .validate import validate_catalog

    problems = [
        problem for problem in validate_catalog(decoded)
        if problem.get("severity") == "error"
    ]
    if problems:
        messages = "; ".join(problem.get("message", "unknown error") for problem in problems)
        raise ValueError(f"refusing to publish invalid asset catalog: {messages}")

    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(serialized, encoding="utf-8")
        written = temporary.read_text(encoding="utf-8")
        round_trip = json.loads(written)
        if round_trip != decoded:
            raise ValueError("asset catalog temporary-file round trip changed payload")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
