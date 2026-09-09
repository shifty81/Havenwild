from __future__ import annotations

import hashlib
import json
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
