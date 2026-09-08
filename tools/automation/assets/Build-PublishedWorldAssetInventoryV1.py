#!/usr/bin/env python3
"""Build Havenwild W41A world-asset truth inventories.

W41A is a diagnostic normalization pass. It does not change runtime/editor
selection. It gathers the competing world-visible asset authorities into a
single deterministic report so W42 can migrate them without guessing.

Generated reports live under WORKSPACE/generated/world_assets and are
regenerable cache/evidence, not source authority.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "havenwild.world_asset_inventory.v1"
STATUS_VALUES = (
    "CERTIFIED",
    "CANDIDATE",
    "PROVISIONAL",
    "PLACEHOLDER",
    "MISSING",
    "LEGACY_ALIAS",
    "REJECTED",
)

# Known semantic mismatches already established by project audits. These are
# intentionally kept here as W41 evidence so "it renders" can never be treated
# as production certification.
REJECTED_SOURCE_RULES = {
    "stairs_up": ("ladder", "Stairs artwork is sourced from a ladder."),
    "bench": ("ottoman", "Bench artwork is sourced from an ottoman."),
    "signboard": ("standing screen", "Sign artwork is sourced from a standing screen."),
    "well_pump": ("water cooler", "Well artwork is sourced from a water cooler."),
}
PLACEHOLDER_IDS = {
    "construction_tape": "Construction tape is a development placeholder, not production greenhouse artwork.",
}

# ObjectKind entries intentionally withheld from normal production exposure.
# These are not palette drift.
OBJECT_KIND_POLICY = {
    "well": {
        "state": "REJECTED",
        "reason": "Quarantined: the former well_pump visual is Water Cooler.png and is not period-appropriate well artwork.",
        "assetPaletteExpected": False,
        "authoringPaletteExpected": False,
    },
    "greenhouse_marker": {
        "state": "PLACEHOLDER",
        "reason": "Development marker currently binds construction_tape; production greenhouse should migrate to a BuildingRecipe.",
        "assetPaletteExpected": True,
        "authoringPaletteExpected": False,
    },
    "cave_entrance": {
        "state": "PROVISIONAL",
        "reason": "No runtime object-atlas binding; this belongs in the structural connector/stamp lane.",
        "assetPaletteExpected": True,
        "authoringPaletteExpected": True,
    },
}


@dataclass
class AssetRecord:
    asset_id: str
    authorities: set[str] = field(default_factory=set)
    scene_refs: list[dict[str, Any]] = field(default_factory=list)
    canonical_placeables: list[dict[str, Any]] = field(default_factory=list)
    lpc_records: list[dict[str, Any]] = field(default_factory=list)
    legacy_records: list[dict[str, Any]] = field(default_factory=list)
    object_kinds: set[str] = field(default_factory=set)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def parse_object_kind_codes(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    result: dict[str, str] = {}
    for variant, code in re.findall(
        r'ObjectKind::([A-Za-z0-9_]+)\s*=>\s*"([a-z0-9_]+)"', text
    ):
        result.setdefault(variant, code)
    return result


def extract_function_body(text: str, name: str) -> str:
    marker = re.search(rf"\bfn\s+{re.escape(name)}\s*\(", text)
    if not marker:
        return ""
    brace = text.find("{", marker.end())
    if brace < 0:
        return ""
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1 : i]
    return text[brace + 1 :]


def parse_object_bindings(path: Path, variant_to_code: dict[str, str]) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    body = extract_function_body(text, "object_asset_binding_for_cell")
    bindings: dict[str, dict[str, Any]] = {}

    for variant in variant_to_code:
        code = variant_to_code[variant]
        # Explicit quarantine/no-binding arm.
        if re.search(rf"ObjectKind::{re.escape(variant)}\s*=>\s*return\s+None", body):
            bindings[code] = {"binding": "none", "stableIds": []}
            continue

        ids: list[str] = []
        simple = re.search(
            rf'ObjectKind::{re.escape(variant)}\s*=>\s*\(\s*\d+\s*,\s*"([^"]+)"\s*\)',
            body,
        )
        if simple:
            ids.append(simple.group(1))
        else:
            arm = re.search(rf"ObjectKind::{re.escape(variant)}\s*=>\s*\{{", body)
            if arm:
                start = arm.end()
                # stop at the next ObjectKind arm or end of match
                nxt = re.search(r"\n\s*ObjectKind::[A-Za-z0-9_]+\s*=>", body[start:])
                segment = body[start : start + nxt.start()] if nxt else body[start:]
                ids.extend(re.findall(r'\(\s*\d+\s*,\s*"([^"]+)"\s*\)', segment))
        if ids:
            bindings[code] = {"binding": "atlas", "stableIds": list(dict.fromkeys(ids))}
    return dict(sorted(bindings.items()))


def parse_palette_object_kinds(path: Path, variant_to_code: dict[str, str], constant_name: str | None = None) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    if constant_name:
        marker = re.search(rf"(?:pub\s+)?const\s+{re.escape(constant_name)}[^=]*=\s*\[", text)
        if marker:
            start = marker.end()
            end = text.find("];", start)
            if end >= 0:
                text = text[start:end]
    variants = re.findall(r"ObjectKind::([A-Za-z0-9_]+)", text)
    codes = [variant_to_code.get(v, v) for v in variants]
    return list(dict.fromkeys(codes))


def scan_canonical_placeables(root: Path, records: dict[str, AssetRecord]) -> dict[str, Any]:
    candidates = [
        root / "content/asset_packs/havenwild_objects/published_world_assets_v1.json",
        root / "content/asset_packs/havenwild_objects/placeables_v1.json",
    ]
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.is_file():
        return {"path": rel(root, path), "present": False, "count": 0, "aliasCount": 0}
    data = load_json(path)
    entries = data.get("entries", [])
    alias_count = 0
    for entry in entries:
        asset_id = str(entry.get("id", "")).strip()
        if not asset_id:
            continue
        rec = records.setdefault(asset_id, AssetRecord(asset_id))
        rec.authorities.add("canonical_placeable_catalog")
        rec.canonical_placeables.append(entry)
        legacy_kind = entry.get("legacy_object_kind")
        if isinstance(legacy_kind, str) and legacy_kind:
            rec.object_kinds.add(legacy_kind)
        for alias in entry.get("aliases", []):
            if not isinstance(alias, str) or not alias.strip():
                continue
            alias = alias.strip()
            alias_count += 1
            alias_rec = records.setdefault(alias, AssetRecord(alias))
            alias_rec.authorities.add("published_world_asset_alias")
            alias_rec.canonical_placeables.append({
                "aliasOf": asset_id,
                "certification": entry.get("certification"),
                "role": entry.get("role"),
            })
            if isinstance(legacy_kind, str) and legacy_kind:
                alias_rec.object_kinds.add(legacy_kind)
    return {
        "path": rel(root, path),
        "present": True,
        "schema": data.get("schema"),
        "count": len(entries),
        "aliasCount": alias_count,
    }


def scan_lpc_manifest(root: Path, records: dict[str, AssetRecord]) -> dict[str, Any]:
    path = root / "assets/generated/havenwild_lpc_objects_160x192_v2.json"
    if not path.is_file():
        return {"path": rel(root, path), "present": False, "count": 0}
    data = load_json(path)
    entries = data.get("objects", data.get("entries", []))
    missing_sources = 0
    for entry in entries:
        asset_id = str(entry.get("id", "")).strip()
        if not asset_id:
            continue
        rec = records.setdefault(asset_id, AssetRecord(asset_id))
        rec.authorities.add("generated_lpc_object_manifest")
        rec.lpc_records.append(entry)
        source = entry.get("source")
        if not isinstance(source, str) or not source or not (root / source).is_file():
            missing_sources += 1
    output = data.get("output")
    source_root = data.get("sourceRoot")
    return {
        "path": rel(root, path),
        "present": True,
        "count": len(entries),
        "atlas": {
            "path": output,
            "exists": bool(isinstance(output, str) and (root / output).is_file()),
        },
        "sourceRoot": {
            "path": source_root,
            "exists": bool(isinstance(source_root, str) and (root / source_root).is_dir()),
        },
        "recordsWithoutPackagedSource": missing_sources,
    }


def scan_legacy_lookup(root: Path, records: dict[str, AssetRecord]) -> dict[str, Any]:
    path = root / "content/worldgen/worldgen_asset_lookup_v0_4.json"
    if not path.is_file():
        return {"path": rel(root, path), "present": False, "count": 0}
    data = load_json(path)
    lookup = data.get("objectAssetLookup", {})
    missing_images = 0
    placeholders = 0
    for key, entry in lookup.items():
        asset_id = str(entry.get("assetId") or key).strip()
        if not asset_id:
            continue
        rec = records.setdefault(asset_id, AssetRecord(asset_id))
        rec.authorities.add("legacy_worldgen_asset_lookup")
        rec.legacy_records.append(entry)
        image = entry.get("image")
        if isinstance(image, str) and image and not (root / image).is_file():
            missing_images += 1
        if str(entry.get("source", "")).lower() == "scene_placeholder":
            placeholders += 1
    return {
        "path": rel(root, path),
        "present": True,
        "count": len(lookup),
        "declaredCoverage": data.get("coverage", {}).get("objectAssets"),
        "declaredPlaceholderCount": data.get("coverage", {}).get("scenePlaceholderObjects"),
        "observedPlaceholderCount": placeholders,
        "missingDeclaredImages": missing_images,
    }


def scan_scenes(root: Path, records: dict[str, AssetRecord]) -> dict[str, Any]:
    scene_root = root / "content/worldgen/scenes"
    files = sorted(scene_root.rglob("*.json")) if scene_root.is_dir() else []
    scene_asset_ids: set[str] = set()
    total_refs = 0
    malformed: list[dict[str, str]] = []
    diagnostic_files = 0
    for path in files:
        try:
            data = load_json(path)
        except Exception as exc:
            malformed.append({"path": rel(root, path), "error": str(exc)})
            continue
        # Acceptance/certification fixtures intentionally repeat or expose
        # identities and must not mutate the production authored-scene migration
        # queue. They are evidence consumers, not content authorities.
        if data.get("role") == "diagnostic_only":
            diagnostic_files += 1
            continue
        objects = data.get("objects", [])
        if not isinstance(objects, list):
            continue
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            asset_id = str(obj.get("assetId", "")).strip()
            if not asset_id:
                continue
            total_refs += 1
            scene_asset_ids.add(asset_id)
            rec = records.setdefault(asset_id, AssetRecord(asset_id))
            rec.authorities.add("authored_scene_reference")
            rec.scene_refs.append(
                {
                    "scene": data.get("sceneId", data.get("id", path.stem)),
                    "sceneFile": rel(root, path),
                    "instanceId": obj.get("id"),
                    "layer": obj.get("layer"),
                    "visualRect": obj.get("visualRect"),
                    "collisionRect": obj.get("collisionRect"),
                    "interactionCount": len(obj.get("interactions", []))
                    if isinstance(obj.get("interactions", []), list)
                    else 0,
                }
            )
    return {
        "root": rel(root, scene_root),
        "sceneFiles": len(files),
        "diagnosticSceneFilesExcluded": diagnostic_files,
        "objectReferences": total_refs,
        "distinctAssetIds": len(scene_asset_ids),
        "malformedScenes": malformed,
    }


def source_status(root: Path, asset_id: str, entry: dict[str, Any]) -> tuple[str | None, str | None]:
    source = str(entry.get("source") or "")
    source_low = source.lower()

    rule = REJECTED_SOURCE_RULES.get(asset_id)
    if rule and rule[0] in source_low:
        return "REJECTED", rule[1]
    if asset_id in PLACEHOLDER_IDS:
        return "PLACEHOLDER", PLACEHOLDER_IDS[asset_id]
    if not source:
        return "MISSING", "Generated LPC record has no authoritative source artwork."

    source_path = root / source
    if source_path.is_file():
        return None, None

    # Complete/source rollups intentionally may omit licensed upstream source
    # mounts while retaining generated runtime atlases plus provenance paths.
    # That is an availability fact, not proof that the asset itself is missing.
    if source.replace("\\", "/").startswith("assets/source/licensed/"):
        return None, None

    return "MISSING", f"Generated LPC source path is missing from the project: {source}"


def classify(root: Path, rec: AssetRecord) -> tuple[str, list[str]]:
    reasons: list[str] = []

    for entry in rec.lpc_records:
        status, reason = source_status(root, rec.asset_id, entry)
        if status:
            reasons.append(reason or status)
            return status, reasons

    # Real LPC source takes precedence over an older legacy placeholder, but the
    # conflict remains visible for migration.
    if rec.scene_refs and rec.lpc_records:
        reasons.append("Authored scene reference has a real LPC-backed candidate; production certification remains incomplete.")
        if any(str(e.get("source", "")).lower() == "scene_placeholder" for e in rec.legacy_records):
            reasons.append("A competing legacy scene_placeholder record must be retired or converted to an alias.")
        return "CANDIDATE", reasons

    for entry in rec.legacy_records:
        if str(entry.get("source", "")).lower() == "scene_placeholder":
            reasons.append("Legacy worldgen lookup explicitly declares source=scene_placeholder.")
            return "PLACEHOLDER", reasons

    if rec.scene_refs and rec.legacy_records:
        missing = []
        for entry in rec.legacy_records:
            image = entry.get("image")
            if isinstance(image, str) and image and not (root / image).is_file():
                missing.append(image)
        if missing:
            reasons.append("Authored scene resolves only through missing legacy artwork: " + ", ".join(sorted(set(missing))))
            return "MISSING", reasons
        reasons.append("Authored scene currently resolves only through the legacy worldgen lookup.")
        return "PROVISIONAL", reasons

    if rec.scene_refs and not (rec.lpc_records or rec.legacy_records or rec.canonical_placeables):
        reasons.append("Authored scene references this identity but no known asset authority defines it.")
        return "MISSING", reasons

    if rec.canonical_placeables:
        reasons.append("Canonical gameplay placeable exists, but PublishedWorldAsset certification does not exist yet.")
        return "PROVISIONAL", reasons

    if rec.lpc_records:
        reasons.append("Real generated LPC source record exists; not yet production-certified.")
        return "CANDIDATE", reasons

    if rec.legacy_records:
        reasons.append("Legacy-only worldgen identity retained for migration/alias analysis.")
        return "LEGACY_ALIAS", reasons

    reasons.append("Discovered identity has no qualifying production authority.")
    return "MISSING", reasons


def source_summary(root: Path, rec: AssetRecord) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for entry in rec.lpc_records:
        source = entry.get("source")
        sources.append(
            {
                "authority": "generated_lpc_object_manifest",
                "path": source,
                "pathExists": bool(isinstance(source, str) and (root / source).is_file()),
                "sourceRect": entry.get("sourceRect"),
                "runtimeRect": entry.get("rect"),
                "footAnchor": entry.get("footAnchor"),
                "sourceMode": entry.get("sourceMode"),
                "placementRole": entry.get("placementRole"),
            }
        )
    for entry in rec.legacy_records:
        image = entry.get("image")
        sources.append(
            {
                "authority": "legacy_worldgen_asset_lookup",
                "sourceMode": entry.get("source"),
                "path": image,
                "pathExists": bool(isinstance(image, str) and (root / image).is_file()),
                "sourceRect": entry.get("rect"),
                "origin": entry.get("origin"),
                "atlas": entry.get("atlas"),
                "json": entry.get("json"),
            }
        )
    return sources


def load_promotion_plan(root: Path) -> dict[str, Any]:
    path = root / "content/assets/lpc/lpc_placeable_object_promotion_plan_v0_1.json"
    if not path.is_file():
        return {"path": rel(root, path), "present": False, "entries": {}}
    data = load_json(path)
    entries = {
        str(e.get("objectKind")): e
        for e in data.get("objectPromotion", [])
        if isinstance(e, dict) and e.get("objectKind")
    }
    return {
        "path": rel(root, path),
        "present": True,
        "version": data.get("version"),
        "entries": entries,
    }


def load_visual_sweep_policy(root: Path) -> dict[str, dict[str, Any]]:
    """Load the current complete ObjectKind visual disposition when available.

    W43B supersedes W41's small hard-coded quarantine list with an explicit
    disposition for every ObjectKind. W41 remains the cross-authority inventory
    validator, so it must recognize those later audited fail-closed decisions
    instead of reporting them as fresh drift.
    """
    path = root / "content/asset_packs/havenwild_objects/placeable_visual_sweep_v1.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    return {
        str(entry.get("objectKind")): entry
        for entry in data.get("entries", [])
        if isinstance(entry, dict) and entry.get("objectKind")
    }


def object_kind_exposure(
    object_codes: list[str],
    bindings: dict[str, dict[str, Any]],
    asset_palette: list[str],
    authoring_palette: list[str],
    promotion_plan: dict[str, Any],
    visual_sweep_policy: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    unexpected: list[dict[str, Any]] = []
    plan_entries = promotion_plan.get("entries", {})

    for code in object_codes:
        policy = dict(OBJECT_KIND_POLICY.get(code, {}))
        sweep = visual_sweep_policy.get(code)
        if sweep:
            # Preserve special W41 palette exposure expectations (Well and the
            # greenhouse development marker), but let the complete W43B sweep
            # become the current status/reason authority for all ObjectKinds.
            policy["state"] = sweep.get("status", policy.get("state", "PROVISIONAL"))
            policy["reason"] = sweep.get("note", policy.get("reason"))
        runtime = bindings.get(code, {"binding": "unknown", "stableIds": []})
        in_asset = code in asset_palette
        in_authoring = code in authoring_palette
        asset_expected = policy.get("assetPaletteExpected", True)
        author_expected = policy.get("authoringPaletteExpected", True)

        issues: list[str] = []
        if in_asset != asset_expected:
            issues.append(f"asset_palette expected={asset_expected} actual={in_asset}")
        if in_authoring != author_expected:
            issues.append(f"authoring_palette expected={author_expected} actual={in_authoring}")

        # Unbound objects must have an explicit policy. This prevents accidental
        # None fallbacks from masquerading as normal content.
        if (
            runtime.get("binding") == "none"
            and code not in OBJECT_KIND_POLICY
            and code not in visual_sweep_policy
        ):
            issues.append("runtime binding is None without an explicit audited quarantine/structural policy")

        row = {
            "objectKind": code,
            "runtimeBinding": runtime,
            "assetPaletteExposed": in_asset,
            "authoringPaletteExposed": in_authoring,
            "policyState": policy.get("state", "PROVISIONAL"),
            "policyReason": policy.get("reason"),
            "assetPaletteExpected": asset_expected,
            "authoringPaletteExpected": author_expected,
            "promotionPlanStatus": plan_entries.get(code, {}).get("promotionStatus"),
            "promotionPlanBinding": plan_entries.get(code, {}).get("currentBinding"),
            "issues": issues,
        }
        rows.append(row)
        if issues:
            unexpected.append(row)

    return rows, unexpected


def build(root: Path) -> dict[str, Any]:
    records: dict[str, AssetRecord] = {}

    authority_state = {
        "canonicalPlaceables": scan_canonical_placeables(root, records),
        "generatedLpcObjects": scan_lpc_manifest(root, records),
        "legacyWorldgenObjects": scan_legacy_lookup(root, records),
        "authoredScenes": scan_scenes(root, records),
    }

    object_catalog = root / "crates/haven_core/src/foundation/tile_object_catalog.rs"
    registry_path = root / "crates/haven_assets/src/asset_registry.rs"
    asset_palette_path = root / "crates/haven_assets/src/asset_palette.rs"
    authoring_palette_path = root / "crates/haven_authoring/src/palette.rs"

    variant_to_code = parse_object_kind_codes(object_catalog)
    object_codes = list(dict.fromkeys(variant_to_code.values()))
    bindings = parse_object_bindings(registry_path, variant_to_code)

    for kind_code, binding in bindings.items():
        for asset_id in binding.get("stableIds", []):
            rec = records.setdefault(asset_id, AssetRecord(asset_id))
            rec.authorities.add("hardcoded_objectkind_visual_binding")
            rec.object_kinds.add(kind_code)

    asset_palette_codes = parse_palette_object_kinds(asset_palette_path, variant_to_code, "PALETTE_OBJECTS")
    authoring_palette_codes = parse_palette_object_kinds(authoring_palette_path, variant_to_code)
    promotion = load_promotion_plan(root)
    visual_sweep_policy = load_visual_sweep_policy(root)
    exposures, exposure_issues = object_kind_exposure(
        object_codes,
        bindings,
        asset_palette_codes,
        authoring_palette_codes,
        promotion,
        visual_sweep_policy,
    )

    inventory: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()

    for asset_id in sorted(records):
        rec = records[asset_id]
        status, reasons = classify(root, rec)
        status_counts[status] += 1
        authority_counts.update(rec.authorities)
        inventory.append(
            {
                "id": asset_id,
                "status": status,
                "statusReasons": reasons,
                "authorities": sorted(rec.authorities),
                "sceneReferenceCount": len(rec.scene_refs),
                "sceneReferences": rec.scene_refs,
                "gameplayObjectKinds": sorted(rec.object_kinds),
                "sourceRecords": source_summary(root, rec),
                "canonicalPlaceableRecords": rec.canonical_placeables,
                "generatedLpcRecords": rec.lpc_records,
                "legacyWorldgenRecords": rec.legacy_records,
            }
        )

    scene_ids = {item["id"] for item in inventory if item["sceneReferenceCount"]}
    placeable_ids = {
        str(entry.get("id"))
        for rec in records.values()
        for entry in rec.canonical_placeables
        if entry.get("id")
    }
    lpc_ids = {
        str(entry.get("id"))
        for rec in records.values()
        for entry in rec.lpc_records
        if entry.get("id")
    }
    legacy_ids = {
        str(entry.get("assetId"))
        for rec in records.values()
        for entry in rec.legacy_records
        if entry.get("assetId")
    }

    conflicts = []
    for item in inventory:
        if len(item["authorities"]) > 1:
            conflicts.append(
                {
                    "id": item["id"],
                    "status": item["status"],
                    "authorities": item["authorities"],
                    "sceneReferenceCount": item["sceneReferenceCount"],
                }
            )

    missing_art = [
        {
            "id": item["id"],
            "status": item["status"],
            "reasons": item["statusReasons"],
            "sceneReferenceCount": item["sceneReferenceCount"],
        }
        for item in inventory
        if item["status"] in {"MISSING", "PLACEHOLDER", "REJECTED"}
    ]

    scene_blockers = [
        item["id"]
        for item in inventory
        if item["sceneReferenceCount"] and item["status"] in {"MISSING", "PLACEHOLDER", "REJECTED"}
    ]
    scene_candidates = [
        item["id"]
        for item in inventory
        if item["sceneReferenceCount"] and item["status"] in {"CANDIDATE", "PROVISIONAL"}
    ]

    migration_queue = {
        "sceneBlockers": scene_blockers,
        "sceneCandidates": scene_candidates,
        "hardcodedBindings": [
            item["id"]
            for item in inventory
            if "hardcoded_objectkind_visual_binding" in item["authorities"]
        ],
        "legacyOnly": [item["id"] for item in inventory if item["status"] == "LEGACY_ALIAS"],
        "objectKindExposureIssues": [row["objectKind"] for row in exposure_issues],
    }

    return {
        "schema": SCHEMA,
        "milestone": "Pass167Z109W41A",
        "purpose": "Normalize world-visible asset evidence before PublishedWorldAsset becomes authority. Diagnostic only; no runtime visual mutation.",
        "statusVocabulary": list(STATUS_VALUES),
        "authorityState": authority_state,
        "rustAuthorityState": {
            "canonicalObjectKindCatalog": rel(root, object_catalog),
            "objectKindCount": len(object_codes),
            "objectKinds": object_codes,
            "objectBindings": bindings,
            "assetPalette": {
                "path": rel(root, asset_palette_path),
                "count": len(asset_palette_codes),
                "objectKinds": asset_palette_codes,
            },
            "sharedAuthoringPalette": {
                "path": rel(root, authoring_palette_path),
                "count": len(authoring_palette_codes),
                "objectKinds": authoring_palette_codes,
            },
            "objectKindExposure": exposures,
            "unexpectedExposureIssues": exposure_issues,
            "historicalPromotionPlan": {
                "path": promotion.get("path"),
                "present": promotion.get("present"),
                "version": promotion.get("version"),
                "note": "Historical promotion metadata is evidence only; later quarantines override stale runtime-bound claims.",
            },
            "legacyWorldgenLoaderHeuristic": "crates/haven_core/src/worldgen_loader.rs::object_kind_from_ids",
            "legacyWorldgenExporterMapping": "crates/haven_core/src/worldgen_exporter.rs::asset_id_for_object",
        },
        "crossAuthority": {
            "sceneIds": len(scene_ids),
            "canonicalPlaceableIds": len(placeable_ids),
            "generatedLpcIds": len(lpc_ids),
            "legacyWorldgenIds": len(legacy_ids),
            "sceneAndCanonicalIntersection": sorted(scene_ids & placeable_ids),
            "sceneAndLpcIntersection": sorted(scene_ids & lpc_ids),
            "sceneAndLegacyIntersection": sorted(scene_ids & legacy_ids),
        },
        "summary": {
            "discoveredAssetIds": len(inventory),
            "statusCounts": dict(sorted(status_counts.items())),
            "authorityMembershipCounts": dict(sorted(authority_counts.items())),
            "conflictingAuthorityIds": len(conflicts),
            "missingOrRejectedIds": len(missing_art),
            "sceneBlockers": len(scene_blockers),
            "sceneCandidates": len(scene_candidates),
            "unexpectedObjectKindExposureIssues": len(exposure_issues),
        },
        "assets": inventory,
        "conflicts": conflicts,
        "missingArt": missing_art,
        "migrationQueue": migration_queue,
    }


def write_outputs(root: Path, report: dict[str, Any]) -> list[Path]:
    out = root / "WORKSPACE/generated/world_assets"
    out.mkdir(parents=True, exist_ok=True)
    payloads = {
        "world_asset_inventory_v1.json": report,
        "world_asset_reference_graph_v1.json": {
            "schema": "havenwild.world_asset_reference_graph.v1",
            "assets": [
                {
                    "id": item["id"],
                    "status": item["status"],
                    "authorities": item["authorities"],
                    "sceneReferences": item["sceneReferences"],
                    "gameplayObjectKinds": item["gameplayObjectKinds"],
                    "sourceRecords": item["sourceRecords"],
                }
                for item in report["assets"]
            ],
        },
        "world_asset_conflicts_v1.json": {
            "schema": "havenwild.world_asset_conflicts.v1",
            "conflicts": report["conflicts"],
            "unexpectedObjectKindExposureIssues": report["rustAuthorityState"]["unexpectedExposureIssues"],
        },
        "world_asset_missing_art_v1.json": {
            "schema": "havenwild.world_asset_missing_art.v1",
            "entries": report["missingArt"],
        },
        "world_asset_migration_queue_v1.json": {
            "schema": "havenwild.world_asset_migration_queue.v1",
            "queue": report["migrationQueue"],
        },
    }
    paths: list[Path] = []
    for name, payload in payloads.items():
        path = out / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="Fail if authored scenes still contain missing/rejected/placeholders or unexpected ObjectKind exposure drift.")
    parser.add_argument("--no-write", action="store_true", help="Audit only; do not emit WORKSPACE-generated evidence.")
    args = parser.parse_args()

    root = (args.root or Path(__file__).resolve().parents[3]).resolve()
    report = build(root)
    written = [] if args.no_write else write_outputs(root, report)

    print(json.dumps(report["summary"], indent=2))
    if written:
        print("Generated:")
        for path in written:
            print(f"  {rel(root, path)}")

    if args.strict:
        failed = False
        if report["migrationQueue"]["sceneBlockers"]:
            failed = True
            print("Strict gate: authored scene blockers remain:")
            for asset_id in report["migrationQueue"]["sceneBlockers"]:
                print(f"  - {asset_id}")
        if report["rustAuthorityState"]["unexpectedExposureIssues"]:
            failed = True
            print("Strict gate: unexpected ObjectKind exposure drift remains:")
            for row in report["rustAuthorityState"]["unexpectedExposureIssues"]:
                print(f"  - {row['objectKind']}: {', '.join(row['issues'])}")
        if failed:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
