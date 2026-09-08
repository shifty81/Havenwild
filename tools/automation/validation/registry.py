from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any

SUPPORTED_SCHEMAS = {
    "havenwild.validator.registry.v2",
    "havenwild.validator.registry.v3",
    "havenwild.validator.registry.v4",
}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_v4_overlay(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    base_ref = data.get("baseRegistry")
    if not base_ref:
        return data
    root = path.parents[2]
    base_path = root / str(base_ref)
    base = _read(base_path)
    if base.get("schema") not in {"havenwild.validator.registry.v2", "havenwild.validator.registry.v3"}:
        raise ValueError(f"v4 base registry must be v2/v3, got {base.get('schema')!r}")

    validators = copy.deepcopy(base.get("validators", []))
    strip = set(data.get("stripProfilesFromBase", []))
    for entry in validators:
        entry["profiles"] = [p for p in entry.get("profiles", []) if p not in strip]

    by_id = {entry.get("id"): entry for entry in validators}
    for addition in data.get("addValidators", []):
        validator_id = addition.get("id")
        if not validator_id:
            raise ValueError("v4 addValidators entry is missing id")
        if validator_id in by_id:
            raise ValueError(f"v4 addValidators duplicates base id: {validator_id}")
        item = copy.deepcopy(addition)
        validators.append(item)
        by_id[validator_id] = item

    for validator_id, patch in data.get("overrides", {}).items():
        if validator_id not in by_id:
            raise ValueError(f"v4 override references unknown id: {validator_id}")
        by_id[validator_id].update(copy.deepcopy(patch))

    assignments = data.get("profileAssignments", {})
    for profile, ids in assignments.items():
        for validator_id in ids:
            if validator_id not in by_id:
                raise ValueError(f"profile {profile!r} references unknown validator {validator_id!r}")
            profiles = by_id[validator_id].setdefault("profiles", [])
            if profile not in profiles:
                profiles.append(profile)

    resolved = copy.deepcopy(data)
    resolved["validators"] = validators
    resolved["resolvedBaseRegistry"] = str(base_ref)
    merged_policy = copy.deepcopy(base.get("policy", {}))
    merged_policy.update(copy.deepcopy(data.get("policy", {})))
    resolved["policy"] = merged_policy
    return resolved


def _validate(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("schema") not in SUPPORTED_SCHEMAS:
        raise ValueError("validator registry schema must be v2, v3, or v4")
    ids: set[str] = set()
    for entry in data.get("validators", []):
        validator_id = entry.get("id")
        if not validator_id or validator_id in ids:
            raise ValueError(f"invalid or duplicate validator id: {validator_id!r}")
        ids.add(validator_id)
        if entry.get("read_only", True) is not True:
            raise ValueError(f"active validator must be read-only: {validator_id}")
    unknown = []
    historical_unknown = []
    live_profiles = {"build", "quick", "source", "framework"}
    for entry in data.get("validators", []):
        for dependency in entry.get("depends_on", []):
            if dependency not in ids:
                relation = f"{entry['id']} -> {dependency}"
                if data.get("schema") == "havenwild.validator.registry.v4" and not (set(entry.get("profiles", [])) & live_profiles):
                    historical_unknown.append(relation)
                else:
                    unknown.append(relation)
    if unknown:
        raise ValueError("unknown live validator dependencies: " + ", ".join(unknown))
    if historical_unknown:
        data["historicalUnknownDependencies"] = historical_unknown
    return data


def load_registry(path: Path) -> dict[str, Any]:
    data = _read(path)
    if data.get("schema") == "havenwild.validator.registry.v4":
        data = _resolve_v4_overlay(path, data)
    return _validate(data)


def topological_order(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {entry["id"]: entry for entry in entries}
    indegree = {key: 0 for key in by_id}
    outgoing = {key: [] for key in by_id}
    for entry in entries:
        for dependency in entry.get("depends_on", []):
            if dependency in by_id:
                indegree[entry["id"]] += 1
                outgoing[dependency].append(entry["id"])
    ready = sorted(
        (key for key, value in indegree.items() if value == 0),
        key=lambda key: (by_id[key].get("order", 0), key),
    )
    ordered = []
    while ready:
        key = ready.pop(0)
        ordered.append(by_id[key])
        for child in outgoing[key]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort(key=lambda item: (by_id[item].get("order", 0), item))
    if len(ordered) != len(entries):
        raise ValueError("validator dependency cycle detected")
    return ordered
