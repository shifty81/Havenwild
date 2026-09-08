from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def load_registry(path: Path) -> dict[str, Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") not in {"havenwild.validator.registry.v2", "havenwild.validator.registry.v3", "havenwild.validator.registry.v4"}:
        raise ValueError("validator registry schema must be v2, v3, or v4")
    ids=set()
    for entry in data.get("validators", []):
        validator_id=entry.get("id")
        if not validator_id or validator_id in ids:
            raise ValueError(f"invalid or duplicate validator id: {validator_id!r}")
        ids.add(validator_id)
    unknown=[]
    for entry in data.get("validators", []):
        for dependency in entry.get("depends_on", []):
            if dependency not in ids:
                unknown.append(f"{entry['id']} -> {dependency}")
    if unknown:
        raise ValueError("unknown validator dependencies: " + ", ".join(unknown))
    return data

def topological_order(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id={entry["id"]:entry for entry in entries}
    indegree={key:0 for key in by_id}
    outgoing={key:[] for key in by_id}
    for entry in entries:
        for dependency in entry.get("depends_on", []):
            if dependency in by_id:
                indegree[entry["id"]]+=1; outgoing[dependency].append(entry["id"])
    ready=sorted((key for key,value in indegree.items() if value==0), key=lambda key: by_id[key].get("order",0))
    ordered=[]
    while ready:
        key=ready.pop(0); ordered.append(by_id[key])
        for child in outgoing[key]:
            indegree[child]-=1
            if indegree[child]==0:
                ready.append(child); ready.sort(key=lambda item: by_id[item].get("order",0))
    if len(ordered)!=len(entries):
        raise ValueError("validator dependency cycle detected")
    return ordered
