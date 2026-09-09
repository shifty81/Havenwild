from __future__ import annotations

from typing import Any


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    if catalog.get("schema") != "pcc.asset.catalog.v1":
        problems.append({"severity": "error", "message": "catalog schema mismatch"})
        return problems

    seen = set()
    for asm in catalog.get("assemblyIndex", []):
        aid = asm.get("assetId")
        if not aid:
            problems.append({"severity": "error", "message": "assembly missing assetId"})
            continue
        if aid in seen:
            problems.append({"severity": "error", "message": f"duplicate assetId: {aid}"})
        seen.add(aid)

        if asm.get("certification") == "runtime_certified" and not asm.get("semantic_role"):
            problems.append({
                "severity": "error",
                "message": f"runtime-certified assembly lacks semantic role: {aid}",
            })
        if asm.get("independently_placeable") == "unproven" and asm.get("certification") == "runtime_certified":
            problems.append({
                "severity": "error",
                "message": f"runtime-certified assembly has unproven placement: {aid}",
            })

    return problems
