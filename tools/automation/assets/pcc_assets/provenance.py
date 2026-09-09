from __future__ import annotations

import hashlib
from pathlib import Path

from .models import SourceRecord
from .pngio import decode_png


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_record(path: Path, source_id: str | None = None) -> SourceRecord:
    width = height = None
    media_type = None
    if path.suffix.lower() == ".png":
        image = decode_png(path)
        width, height = image.width, image.height
        media_type = "image/png"
    elif path.suffix.lower() in {".tsx", ".tmx"}:
        media_type = "application/xml"
    return SourceRecord(
        path=path.as_posix(),
        sha256=sha256_file(path),
        bytes=path.stat().st_size,
        width=width,
        height=height,
        media_type=media_type,
        source_id=source_id,
    )
