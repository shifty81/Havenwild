from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
REGISTRY = ROOT / "content/build/generated_output_registry_v2.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    failures = []
    verified = 0
    pending = 0
    for entry in registry["outputs"]:
        output = ROOT / entry["output"]
        sidecar = ROOT / entry["provenance"]
        if not output.exists():
            pending += 1
            continue
        if not sidecar.exists():
            failures.append(f"{entry['output']}: missing provenance sidecar {entry['provenance']}")
            continue
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        if payload.get("generator_id") != entry["generator_id"]:
            failures.append(f"{entry['output']}: generator id mismatch")
        if payload.get("generator_version") != entry["generator_version"]:
            failures.append(f"{entry['output']}: generator version mismatch")
        if payload.get("output_sha256") != digest(output):
            failures.append(f"{entry['output']}: output digest mismatch")
        recorded_inputs = payload.get("inputs", {})
        for item in entry.get("inputs", []):
            path = ROOT / item
            if path.is_file() and recorded_inputs.get(item) != digest(path):
                failures.append(f"{entry['output']}: stale input digest for {item}")
        verified += 1
    if failures:
        print("Generated-output provenance validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Pass 146D generated-output provenance valid: {verified} verified, {pending} pending generation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
