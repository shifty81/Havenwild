from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json

@dataclass(frozen=True)
class FreshnessState:
    output: str
    status: str
    newest_input_mtime_ns: int
    output_mtime_ns: int
    missing_inputs: tuple[str, ...]

def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def inspect_output(root: Path, entry: dict) -> FreshnessState:
    output=root/entry["output"]
    inputs=[root/item for item in entry.get("inputs", [])]
    missing=tuple(str(path.relative_to(root)) for path in inputs if not path.exists())
    newest=max((path.stat().st_mtime_ns for path in inputs if path.exists()), default=0)
    output_mtime=output.stat().st_mtime_ns if output.exists() else 0
    if missing:
        status="missing-inputs"
    elif not output.exists():
        status="regenerate" if entry.get("packaging") in {"regenerate","cache-or-regenerate"} else "missing-output"
    elif output_mtime < newest:
        status="stale"
    else:
        status="fresh"
    return FreshnessState(entry["output"],status,newest,output_mtime,missing)

def provenance(root: Path, entry: dict) -> dict:
    return {
        "schema":"havenwild.generated.provenance.v1",
        "output":entry["output"],
        "generator":entry["generator"],
        "inputs":{item:sha256(root/item) for item in entry.get("inputs",[]) if (root/item).is_file()},
    }
