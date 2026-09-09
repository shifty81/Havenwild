from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class AssetService:
    service_id: str
    domain: str
    description: str
    mutates_project: bool
    certification_required: bool
    replaces_targets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["replacesTargets"] = list(self.replaces_targets)
        out.pop("replaces_targets", None)
        return out


SERVICES: tuple[AssetService, ...] = (
    AssetService(
        "assets.intake.manifest", "intake",
        "Inventory a source folder/file/ZIP with hashes and provenance evidence.",
        False, False, ("intake",),
    ),
    AssetService(
        "assets.catalog.scan", "catalog",
        "Build the canonical project-independent asset catalog.",
        False, False, ("catalog",),
    ),
    AssetService(
        "assets.analyze.sheet", "analyze",
        "Analyze sprite sheets, cells, seams, assemblies, repeats and animation candidates.",
        False, False, ("analyze", "terrain", "character"),
    ),
    AssetService(
        "assets.metadata.tiled", "analyze",
        "Parse TSX/TMX terrain/Wang, animation, collision and property evidence.",
        False, False, ("analyze", "terrain"),
    ),
    AssetService(
        "assets.provenance.audit", "provenance",
        "Record source hashes, credits/license evidence and lineage.",
        False, False, ("provenance",),
    ),
    AssetService(
        "assets.prefab.extract", "prefab",
        "Promote source-native multi-cell assemblies into prefab candidates.",
        False, True, ("prefab",),
    ),
    AssetService(
        "assets.prefab.generate", "prefab",
        "Generate semantic prefab recipes only from mapped/certified roles.",
        False, True, ("prefab",),
    ),
    AssetService(
        "assets.certification.queue", "certify",
        "Build a review queue from candidates without auto-certifying them.",
        False, True, ("certify", "review"),
    ),
    AssetService(
        "assets.derive.plan", "derive",
        "Plan derived atlases/caches with source-lineage requirements.",
        False, True, ("derive",),
    ),
    AssetService(
        "assets.promote.plan", "promote",
        "Plan promotion only for explicitly runtime-certified records.",
        False, True, ("promote",),
    ),
    AssetService(
        "assets.validate.catalog", "validate",
        "Run shared canonical catalog validation rules.",
        False, False, ("validate",),
    ),
    AssetService(
        "assets.migration.plan", "migration",
        "Group legacy tools into parity-safe normalization batches.",
        False, False,
    ),
)


def service_registry() -> dict[str, Any]:
    return {
        "schema": "pcc.asset.service_registry.v1",
        "services": [service.to_dict() for service in SERVICES],
    }


def services_for_target(target: str) -> list[str]:
    return [
        service.service_id
        for service in SERVICES
        if target in service.replaces_targets
    ]
