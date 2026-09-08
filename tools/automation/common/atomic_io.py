from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import os
import tempfile
from typing import Any, Iterator


def _replace(temp_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temp_path, destination)


@contextmanager
def atomic_path(destination: Path) -> Iterator[Path]:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temp_path = Path(raw)
    try:
        yield temp_path
        if not temp_path.exists():
            raise RuntimeError(f"atomic writer did not create temporary output: {temp_path}")
        _replace(temp_path, destination)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise



def atomic_write_bytes(destination: Path, data: bytes) -> None:
    with atomic_path(destination) as temp_path:
        temp_path.write_bytes(data)


def atomic_write_text(destination: Path, text: str, *, encoding: str = "utf-8") -> None:
    with atomic_path(destination) as temp_path:
        temp_path.write_text(text, encoding=encoding)


def atomic_write_json(destination: Path, payload: Any) -> None:
    atomic_write_text(destination, json.dumps(payload, indent=2) + "\n")


def atomic_save_image(image: Any, destination: Path, **save_options: Any) -> None:
    destination = Path(destination)
    image_format = save_options.pop("format", None) or destination.suffix.lstrip(".").upper()
    if image_format == "JPG":
        image_format = "JPEG"
    with atomic_path(destination) as temp_path:
        image.save(temp_path, format=image_format, **save_options)
