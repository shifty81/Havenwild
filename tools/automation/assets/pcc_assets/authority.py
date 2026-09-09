from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import CertificationState


def _iter_assemblies(catalog: dict[str, Any]):
    for sheet in catalog.get("sheets", []):
        source = sheet.get("source", {})
        for assembly in sheet.get("assemblies", []):
            yield source, assembly


def build_certification_queue(catalog: dict[str, Any]) -> dict[str, Any]:
    records = []
    for source, assembly in _iter_assemblies(catalog):
        state = assembly.get("certification", CertificationState.CANDIDATE.value)
        if state in {
            CertificationState.RUNTIME_CERTIFIED.value,
            CertificationState.REJECTED.value,
            CertificationState.DEPRECATED.value,
        }:
            continue
        records.append({
            "candidateType": "assembly",
            "sourcePath": source.get("path"),
            "sourceSha256": source.get("sha256"),
            "assemblyId": assembly.get("assembly_id") or assembly.get("assemblyId"),
            "footprint": assembly.get("footprint"),
            "sourceRectPx": assembly.get("source_rect_px") or assembly.get("sourceRectPx"),
            "currentCertification": state,
            "semanticRole": assembly.get("semantic_role") or assembly.get("semanticRole"),
            "independentlyPlaceable": (
                assembly.get("independently_placeable")
                if "independently_placeable" in assembly
                else assembly.get("independentlyPlaceable", "unproven")
            ),
            "requiredEvidence": [
                "source lineage",
                "semantic role",
                "placement/neighbor contract",
                "anchor/collision contract when applicable",
            ],
        })
    return {
        "schema": "pcc.asset.certification_queue.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "summary": {"candidateCount": len(records)},
        "candidates": records,
        "policy": {"automaticCertification": False},
    }


def build_promotion_plan(catalog: dict[str, Any]) -> dict[str, Any]:
    promote = []
    blocked = []
    for source, assembly in _iter_assemblies(catalog):
        state = assembly.get("certification", CertificationState.CANDIDATE.value)
        record = {
            "sourcePath": source.get("path"),
            "sourceSha256": source.get("sha256"),
            "assemblyId": assembly.get("assembly_id") or assembly.get("assemblyId"),
            "certification": state,
        }
        if state == CertificationState.RUNTIME_CERTIFIED.value:
            promote.append(record)
        else:
            record["reason"] = "runtime_certified required"
            blocked.append(record)
    return {
        "schema": "pcc.asset.promotion_plan.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "promotionCount": len(promote),
            "blockedCount": len(blocked),
        },
        "promote": promote,
        "blocked": blocked,
        "policy": {
            "projectFilesModified": False,
            "derivedFilesWritten": False,
            "certificationRequired": CertificationState.RUNTIME_CERTIFIED.value,
        },
    }


def build_derive_plan(catalog: dict[str, Any]) -> dict[str, Any]:
    tasks = []
    for source, assembly in _iter_assemblies(catalog):
        tasks.append({
            "operation": "derive_candidate",
            "sourcePath": source.get("path"),
            "sourceSha256": source.get("sha256"),
            "assemblyId": assembly.get("assembly_id") or assembly.get("assemblyId"),
            "certification": assembly.get("certification", "candidate"),
            "lineageRequired": True,
            "writeAllowed": False,
        })
    return {
        "schema": "pcc.asset.derive_plan.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "summary": {"candidateTaskCount": len(tasks)},
        "tasks": tasks,
        "policy": {
            "planningOnly": True,
            "runtimeDerivativeRequiresCertifiedSource": True,
        },
    }


def build_prefab_library(catalog: dict[str, Any]) -> dict[str, Any]:
    prefabs = []
    for source, assembly in _iter_assemblies(catalog):
        footprint = assembly.get("footprint") or [1, 1]
        if not isinstance(footprint, list) or len(footprint) != 2:
            continue
        if int(footprint[0]) * int(footprint[1]) <= 1:
            continue
        prefabs.append({
            "prefabId": f"source:{source.get('sha256','unknown')[:12]}:{assembly.get('assembly_id') or assembly.get('assemblyId')}",
            "kind": "source_native_multitile",
            "sourcePath": source.get("path"),
            "sourceSha256": source.get("sha256"),
            "assemblyId": assembly.get("assembly_id") or assembly.get("assemblyId"),
            "footprint": footprint,
            "sourceRectPx": assembly.get("source_rect_px") or assembly.get("sourceRectPx"),
            "certification": assembly.get("certification", "candidate"),
            "semanticRole": assembly.get("semantic_role") or assembly.get("semanticRole"),
            "ready": assembly.get("certification") == CertificationState.RUNTIME_CERTIFIED.value,
        })

    house_templates = [
        {"prefabId": "grammar:house:small", "kind": "semantic_house_grammar", "footprint": [5, 6]},
        {"prefabId": "grammar:house:medium", "kind": "semantic_house_grammar", "footprint": [7, 8]},
        {"prefabId": "grammar:house:large", "kind": "semantic_house_grammar", "footprint": [9, 11]},
    ]
    for item in house_templates:
        item.update({
            "ready": False,
            "certification": "candidate",
            "rule": "Requires project adapter role map; missing visual roles remain unresolved, never invented.",
        })

    return {
        "schema": "pcc.asset.prefab_library.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "sourceNativePrefabCount": len(prefabs),
            "houseGrammarTemplateCount": len(house_templates),
        },
        "sourceNativePrefabs": prefabs,
        "grammarTemplates": house_templates,
        "policy": {
            "sourcePixelsPreserved": True,
            "automaticSemanticGuessing": False,
        },
    }
