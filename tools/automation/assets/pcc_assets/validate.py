from __future__ import annotations

from typing import Any


SUPPORTED_SCHEMAS = {
    "pcc.asset.catalog.v1",
    "pcc.asset.catalog.v2",
}


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    schema = catalog.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        problems.append({
            "severity": "error",
            "message": f"catalog schema mismatch: {schema}",
        })
        return problems

    summary = catalog.get("summary")
    if not isinstance(summary, dict):
        problems.append({
            "severity": "error",
            "message": "catalog summary missing",
        })

    seen = set()
    for asm in catalog.get("assemblyIndex", []):
        aid = asm.get("assetId")
        if not aid:
            problems.append({
                "severity": "error",
                "message": "assembly missing assetId",
            })
            continue
        if aid in seen:
            problems.append({
                "severity": "error",
                "message": f"duplicate assetId: {aid}",
            })
        seen.add(aid)

        certification = asm.get("certification")
        semantic_role = (
            asm.get("semantic_role")
            if "semantic_role" in asm
            else asm.get("semanticRole")
        )
        independently_placeable = (
            asm.get("independently_placeable")
            if "independently_placeable" in asm
            else asm.get("independentlyPlaceable")
        )
        if certification == "runtime_certified" and not semantic_role:
            problems.append({
                "severity": "error",
                "message": (
                    "runtime-certified assembly lacks semantic role: "
                    f"{aid}"
                ),
            })
        if (
            independently_placeable == "unproven"
            and certification == "runtime_certified"
        ):
            problems.append({
                "severity": "error",
                "message": (
                    "runtime-certified assembly has unproven placement: "
                    f"{aid}"
                ),
            })

    storage = catalog.get("storage")
    if isinstance(storage, dict) and storage.get("mode") == "compact":
        if not storage.get("detailStore"):
            problems.append({
                "severity": "error",
                "message": "compact catalog missing SQLite detailStore",
            })

    return problems
