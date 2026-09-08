from __future__ import annotations
import json
from pathlib import Path

ALIASES = Path("content/validation/validator_aliases_v1.json")


def resolve_profile(root: Path, requested: str) -> str:
    path = root / ALIASES
    if not path.is_file():
        return requested
    data = json.loads(path.read_text(encoding="utf-8"))
    aliases = data.get("profiles", {})
    seen: set[str] = set()
    value = requested
    while value in aliases:
        if value in seen:
            raise ValueError(f"profile alias cycle detected at {value!r}")
        seen.add(value)
        value = str(aliases[value])
    return value
