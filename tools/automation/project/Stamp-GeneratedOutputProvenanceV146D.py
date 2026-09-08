from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "automation"))
from common.atomic_io import atomic_write_json

REGISTRY = ROOT / "content/build/generated_output_registry_v2.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stamped = 0
    skipped = 0
    for entry in registry["outputs"]:
        output = ROOT / entry["output"]
        if not output.is_file():
            skipped += 1
            continue
        inputs = {}
        missing = []
        for item in entry.get("inputs", []):
            path = ROOT / item
            if path.is_file():
                inputs[item] = digest(path)
            else:
                missing.append(item)
        if missing:
            print(f"Cannot stamp {entry['output']}: missing inputs {missing}", file=sys.stderr)
            return 1
        sidecar = ROOT / entry["provenance"]
        payload = {
            "schema": "havenwild.generated.provenance.v1",
            "generator_id": entry["generator_id"],
            "generator_version": entry["generator_version"],
            "schema_version": entry.get("output_schema_version", 1),
            "generator": entry["generator"],
            "source_lock": entry.get("source_lock"),
            "output": entry["output"],
            "output_sha256": digest(output),
            "inputs": inputs,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "atomic_write_required": True,
        }
        atomic_write_json(sidecar, payload)
        stamped += 1
    print(f"Stamped generated-output provenance: {stamped} output(s), {skipped} absent optional output(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
