#!/usr/bin/env python3
"""Index the complete pinned Universal LPC character repository for Havenwild.

The raw repository remains an immutable local dependency. This tool creates
stable, searchable metadata for every spritesheet and sheet definition, plus
small equipment/action catalogs consumed by the editor and runtime cache
builder. It never copies or flattens third-party source artwork.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "content/assets/intake/universal_lpc_generator_source_lock_v0_1.json"
SOURCE = ROOT / "assets/source/licensed/universal_lpc_generator"
OUTPUT = ROOT / "content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz"
SUMMARY = ROOT / "content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json"
EQUIPMENT = ROOT / "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json"
GAMEPLAY = ROOT / "content/assets/lpc/universal_lpc_gameplay_item_seed_catalog_v0_1.json"
REVISION = ROOT / "WORKSPACE/generated/.universal_lpc_complete_repository_revision"

ANIMATIONS = (
    "spellcast", "thrust", "walk", "slash", "shoot", "hurt", "watering",
    "idle", "jump", "run", "sit", "emote", "climb", "combat",
    "1h_slash", "1h_backslash", "1h_halfslash",
)
BODIES = ("male", "muscular", "female", "pregnant", "teen", "child")
TOOL_PATH_IDS = {
    "axe": "axe",
    "pickaxe": "pickaxe",
    "hoe": "hoe",
    "hammer": "hammer",
    "shovel": "shovel",
    "whip": "whip",
    "watering_can": "watering_can",
    "fishing_rod": "fishing_rod",
}


def normalized_path_segments(path: str) -> list[str]:
    return [segment for segment in path.lower().replace("\\", "/").split("/") if segment]


def tool_id_for_path(path: str) -> str | None:
    parts = normalized_path_segments(path)
    if "tools" in parts:
        index = parts.index("tools")
        tail = parts[index + 1:]
        if tail:
            first = tail[0]
            if first in TOOL_PATH_IDS:
                return TOOL_PATH_IDS[first]
            if first == "watering" and "can" in tail[:2]:
                return "watering_can"
            if first == "fishing" and "rod" in tail[:2]:
                return "fishing_rod"
    # Scythes are weapons in the source hierarchy but are also a Havenwild work tool.
    for index, part in enumerate(parts[:-1]):
        if part in {"weapon", "weapons"} and "scythe" in parts[index + 1:]:
            return "scythe"
    return None



def stable_id(provider: str, relative: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", relative.lower()).strip(".")
    digest = hashlib.sha1(relative.encode("utf-8")).hexdigest()[:12]
    return f"{provider}.{slug}.{digest}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def animation_tokens(path: str, definition: dict[str, Any] | None = None) -> list[str]:
    lower = path.lower().replace("-", "_")
    found = {name for name in ANIMATIONS if name in lower}
    if definition:
        for value in definition.get("animations", []):
            if isinstance(value, str):
                found.add(value)
    return sorted(found)


def body_tokens(path: str, definition: dict[str, Any] | None = None) -> list[str]:
    lower = path.lower()
    found = {body for body in BODIES if f"/{body}/" in f"/{lower}/" or f"_{body}" in lower}
    if definition:
        for key, value in definition.items():
            if not key.startswith("layer_") or not isinstance(value, dict):
                continue
            for body in BODIES:
                if isinstance(value.get(body), str):
                    found.add(body)
    return sorted(found)


def semantic_roles(path: str) -> list[str]:
    p = path.lower().replace("\\", "/")
    roles: set[str] = set()
    checks = {
        "body": ("/body/", "/bodies/"),
        "head": ("/head/", "/heads/"),
        "eyes": ("/eyes/",),
        "hair": ("/hair/", "/beards/", "/mustaches/"),
        "clothing": ("/torso/", "/legs/", "/feet/", "/clothes/", "/clothing/"),
        "armor": ("/armor/", "/armour/"),
        "headwear": ("/headwear/", "/hat", "/helmet"),
        "tool": ("/tools/", "axe", "pickaxe", "watering", "hoe", "hammer", "scythe", "fishing"),
        "weapon": ("/weapons/", "sword", "spear", "bow", "dagger", "mace", "staff"),
        "shield": ("/shield",),
        "wings": ("/wings/",),
        "accessory": ("/accessories/", "/jewelry/", "/jewellery/"),
    }
    for role, tokens in checks.items():
        if any(token in p for token in tokens):
            roles.add(role)
    if not roles:
        roles.add("character_layer")
    return sorted(roles)



def definition_layers(definition: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for key, value in definition.items():
        if not key.startswith("layer_") or not isinstance(value, dict):
            continue
        body_paths = {body: value[body] for body in BODIES if isinstance(value.get(body), str)}
        result.append({"name": key, "zPos": int(value.get("zPos", 0)), "bodyPaths": body_paths})
    return sorted(result, key=lambda item: (item["zPos"], item["name"]))


def credit_rows(source: Path) -> tuple[list[dict[str, str]], dict[str, list[int]]]:
    path = source / "CREDITS.csv"
    if not path.is_file():
        return [], {}
    rows: list[dict[str, str]] = []
    by_file: dict[str, list[int]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as stream:
        for index, row in enumerate(csv.DictReader(stream)):
            clean = {str(k): str(v or "").strip() for k, v in row.items() if k is not None}
            rows.append(clean)
            candidate = clean.get("file") or clean.get("File") or clean.get("path") or clean.get("Path") or ""
            if candidate:
                by_file[candidate.replace("\\", "/").lower()].append(index)
    return rows, dict(by_file)


def nearest_credit_indices(relative: str, by_file: dict[str, list[int]]) -> list[int]:
    lower = relative.lower()
    matches: list[tuple[int, list[int]]] = []
    for key, rows in by_file.items():
        normalized = key.rstrip("/")
        if normalized and (lower == normalized or lower.startswith(normalized + "/") or normalized in lower):
            matches.append((len(normalized), rows))
    return list(max(matches, default=(0, []), key=lambda item: item[0])[1])


def classify_equipment(record: dict[str, Any]) -> dict[str, Any] | None:
    roles = set(record.get("semanticRoles", []))
    if not roles.intersection({"tool", "weapon", "shield", "armor", "clothing", "headwear", "accessory"}):
        return None
    tool_id = tool_id_for_path(record["relativePath"])
    return {
        "stableId": record["stableId"],
        "sourcePath": record["relativePath"],
        "roles": record["semanticRoles"],
        "bodyFamilies": record.get("bodyFamilies", []),
        "animations": record.get("animations", []),
        "toolId": tool_id,
        "creditRecordIndices": record.get("creditRecordIndices", []),
        "productionState": "eligible_after_runtime_compatibility_and_license_validation",
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_gzip(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as stream:
        json.dump(value, stream, separators=(",", ":"))


def build(source: Path, fixture: bool) -> dict[str, Any]:
    lock = read_json(LOCK_PATH)
    if not source.is_dir():
        raise RuntimeError(f"Universal LPC source is not mounted: {source}")
    for relative in lock["requiredTopLevelPaths"]:
        if not (source / relative).exists():
            raise RuntimeError(f"Universal LPC source is missing required path: {relative}")

    credits, credits_by_file = credit_rows(source)
    records: list[dict[str, Any]] = []
    definitions: list[dict[str, Any]] = []
    role_counts: Counter[str] = Counter()
    animation_counts: Counter[str] = Counter()
    body_counts: Counter[str] = Counter()

    for path in sorted((source / "sheet_definitions").rglob("*.json")):
        relative = path.relative_to(source).as_posix()
        try:
            definition = read_json(path)
        except Exception as error:
            definitions.append({"stableId": stable_id("ulpc.definition", relative), "relativePath": relative, "parseError": str(error)})
            continue
        roles = semantic_roles(relative)
        animations = animation_tokens(relative, definition)
        bodies = body_tokens(relative, definition)
        for role in roles: role_counts[role] += 1
        for item in animations: animation_counts[item] += 1
        for item in bodies: body_counts[item] += 1
        definitions.append({
            "stableId": stable_id("ulpc.definition", relative),
            "relativePath": relative,
            "name": definition.get("name", path.stem),
            "typeName": definition.get("type_name"),
            "priority": definition.get("priority"),
            "semanticRoles": roles,
            "animations": animations,
            "bodyFamilies": bodies,
            "layers": definition_layers(definition),
            "credits": definition.get("credits", []),
            "recolors": definition.get("recolors"),
        })

    for path in sorted((source / "spritesheets").rglob("*.png")):
        relative = path.relative_to(source).as_posix()
        roles = semantic_roles(relative)
        animations = animation_tokens(relative)
        bodies = body_tokens(relative)
        for role in roles: role_counts[role] += 1
        for item in animations: animation_counts[item] += 1
        for item in bodies: body_counts[item] += 1
        records.append({
            "stableId": stable_id("ulpc.sprite", relative),
            "relativePath": relative,
            "semanticRoles": roles,
            "animations": animations,
            "bodyFamilies": bodies,
            "creditRecordIndices": nearest_credit_indices(relative, credits_by_file),
            "sourceAuthority": "universal_lpc_character_generator",
            "productionState": "cataloged_compatibility_gated",
        })

    palettes = [path.relative_to(source).as_posix() for path in sorted((source / "palette_definitions").rglob("*.json"))]
    counts = {
        "spritesheetPngFiles": len(records),
        "sheetDefinitionJsonFiles": len(definitions),
        "paletteDefinitionJsonFiles": len(palettes),
        "creditRecords": len(credits),
    }
    expected = lock["expectedInventory"]
    if not fixture:
        for key in ("spritesheetPngFiles", "sheetDefinitionJsonFiles", "creditRecords"):
            if counts[key] != expected[key]:
                raise RuntimeError(f"Universal LPC inventory mismatch for {key}: {counts[key]} != {expected[key]}")

    equipment = [entry for entry in (classify_equipment(record) for record in records) if entry]
    tool_groups: dict[str, list[str]] = defaultdict(list)
    for item in equipment:
        if item["toolId"]:
            tool_groups[item["toolId"]].append(item["stableId"])

    index = {
        "schema": "havenwild.universal_lpc.complete_repository_index.v0_1",
        "source": {"repository": lock["repository"], "commit": lock["commit"], "mount": lock["mountProjectPath"]},
        "counts": counts,
        "spritesheets": records,
        "sheetDefinitions": definitions,
        "paletteDefinitions": palettes,
        "creditRecords": credits,
    }
    equipment_catalog = {
        "schema": "havenwild.universal_lpc.equipment_action_catalog.v0_1",
        "sourceCommit": lock["commit"],
        "records": equipment,
        "toolBindings": {key: value for key, value in sorted(tool_groups.items())},
        "runtimePolicy": "stable source record plus exact body/animation compatibility",
    }
    gameplay_catalog = {
        "schema": "havenwild.universal_lpc.gameplay_item_seed_catalog.v0_1",
        "sourceCommit": lock["commit"],
        "tools": [{"id": key, "sourceAssetIds": value} for key, value in sorted(tool_groups.items())],
        "equipmentAssetIds": [item["stableId"] for item in equipment],
        "policy": "catalog seeds only; gameplay stats remain Havenwild-authored data",
    }
    summary = {
        "schema": "havenwild.universal_lpc.complete_repository_summary.v0_1",
        "sourceCommit": lock["commit"],
        "counts": counts,
        "semanticRoleCounts": dict(sorted(role_counts.items())),
        "animationCounts": dict(sorted(animation_counts.items())),
        "bodyFamilyCounts": dict(sorted(body_counts.items())),
        "equipmentRecords": len(equipment),
        "toolGroups": {key: len(value) for key, value in sorted(tool_groups.items())},
        "strictCertified": not fixture,
    }
    write_gzip(OUTPUT, index)
    write_json(SUMMARY, summary)
    write_json(EQUIPMENT, equipment_catalog)
    write_json(GAMEPLAY, gameplay_catalog)
    REVISION.parent.mkdir(parents=True, exist_ok=True)
    REVISION.write_text(lock["commit"] + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--fixture", action="store_true", help="allow reduced fixture inventories")
    args = parser.parse_args()
    summary = build(args.source.resolve(), args.fixture)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
