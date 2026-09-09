from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .services import services_for_target, service_registry

PHASES = {
    "intake": "P0",
    "catalog": "P0",
    "provenance": "P0",
    "analyze": "P0",
    "prefab": "P0",
    "derive": "P1",
    "promote": "P1",
    "certify": "P1",
    "terrain": "P1",
    "character": "P1",
    "validate": "P2",
    "review": "P2",
    "audio": "P2",
}

# High-value tools that should be used as parity donors early instead of
# waiting for arbitrary filename order.
DONOR_PRIORITY = (
    "Generate-AssetCatalog.py",
    "Catalog-ExternalSpriteLibrary.py",
    "Prepare-ExternalAssetPack.py",
    "Build-ElizaWyProjectAssetAuditV167Z38.py",
    "Build-ElizaWyExternalPackIndexV1.py",
    "Build-HavenwildAssetUtilizationAuditV115.py",
    "Build-OgaLpcCliffCatalogV167Q.py",
    "Promote-LpcRuntimeAssets.py",
    "Build-StructureSourceInventoryV1.py",
    "Build-StructureComponentCertificationV1.py",
    "Build-BuildingRecipeAcceptanceSceneV1.py",
    "Validate-GenericMultitileStampSystemV78.py",
    "Validate-StructureSourceInventoryV1.py",
    "Validate-BuildingRecipeAuthorityV1.py",
    "Validate-PccAssetSystemV1.py",
)


def _priority(path: str, target: str) -> int:
    name = path.rsplit("/", 1)[-1]
    if name in DONOR_PRIORITY:
        return 0
    if target in {"intake", "catalog", "provenance", "analyze", "prefab"}:
        return 10
    if target in {"derive", "promote", "certify", "terrain", "character"}:
        return 20
    return 30


def build_normalization_plan(inventory: dict[str, Any]) -> dict[str, Any]:
    if inventory.get("schema") != "pcc.asset.legacy_tool_inventory.v1":
        raise ValueError("expected pcc.asset.legacy_tool_inventory.v1")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tool in inventory.get("tools", []):
        target = tool.get("normalizationTarget", "review")
        grouped[target].append(tool)

    batches = []
    for target in sorted(grouped, key=lambda t: (PHASES.get(t, "P9"), t)):
        tools = sorted(
            grouped[target],
            key=lambda item: (_priority(item.get("path", ""), target), item.get("path", "")),
        )
        batches.append({
            "batchId": f"{PHASES.get(target,'P9')}-{target}",
            "phase": PHASES.get(target, "P9"),
            "target": target,
            "canonicalServices": services_for_target(target),
            "toolCount": len(tools),
            "tools": [
                {
                    "path": item.get("path"),
                    "recommendedAction": item.get("recommendedAction"),
                    "parityState": "not_started",
                    "priority": _priority(item.get("path", ""), target),
                }
                for item in tools
            ],
        })

    unresolved_targets = sorted(
        target for target in grouped
        if not services_for_target(target)
    )

    return {
        "schema": "pcc.asset.normalization_plan.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceInventory": {
            "toolCount": inventory.get("summary", {}).get("toolCount"),
            "byNormalizationTarget": inventory.get("summary", {}).get("byNormalizationTarget", {}),
        },
        "policy": {
            "deleteExistingToolsAutomatically": False,
            "migrationMethod": "extract -> parity -> wrapper -> PCC command -> archive",
            "legacyAuthorityPreservedUntilParity": True,
            "massValidatorRewriteForbidden": True,
        },
        "serviceRegistry": service_registry(),
        "summary": {
            "batchCount": len(batches),
            "unresolvedServiceTargets": unresolved_targets,
        },
        "batches": batches,
    }


def select_normalization_batch(
    inventory: dict[str, Any],
    target: str,
    limit: int = 25,
) -> dict[str, Any]:
    plan = build_normalization_plan(inventory)
    matches = [b for b in plan["batches"] if b["target"] == target]
    if not matches:
        raise ValueError(f"normalization target not found: {target}")
    batch = dict(matches[0])
    batch["tools"] = batch["tools"][:max(1, int(limit))]
    batch["toolCount"] = len(batch["tools"])
    return {
        "schema": "pcc.asset.normalization_batch.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "canonicalServices": batch["canonicalServices"],
        "toolCount": batch["toolCount"],
        "tools": batch["tools"],
        "policy": plan["policy"],
    }
