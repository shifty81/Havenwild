from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CertificationState(str, Enum):
    UNCLASSIFIED = "unclassified"
    CANDIDATE = "candidate"
    SOURCE_REFERENCE = "source_reference"
    METADATA_VERIFIED = "metadata_verified"
    EXAMPLE_VERIFIED = "example_verified"
    RUNTIME_CERTIFIED = "runtime_certified"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class GridSpec:
    cell_width: int
    cell_height: int
    columns: int
    rows: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceRecord:
    path: str
    sha256: str
    bytes: int
    width: int | None = None
    height: int | None = None
    media_type: str | None = None
    source_id: str | None = None
    license_id: str | None = None
    attribution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CellRecord:
    cell_id: str
    column: int
    row: int
    occupied_pixels: int
    occupancy_ratio: float
    alpha_bbox: list[int] | None
    rgba_hash: str
    alpha_hash: str
    classification: str = "unclassified"
    assembly_ids: list[str] = field(default_factory=list)
    exact_duplicate_group: str | None = None
    alpha_duplicate_group: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeamRecord:
    a: str
    b: str
    direction: str
    touching_pixels: int
    color_continuity_pixels: int
    occupied_boundary_positions: int
    continuity_score: float
    connected: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssemblyCandidate:
    assembly_id: str
    members: list[str]
    bounds_cells: list[int]
    footprint: list[int]
    source_rect_px: list[int]
    seam_count: int
    occupancy_ratio: float
    independently_placeable: str = "unproven"
    semantic_role: str | None = None
    anchor: list[int] | None = None
    repeatable_x: bool = False
    repeatable_y: bool = False
    certification: CertificationState = CertificationState.CANDIDATE
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["certification"] = self.certification.value
        return out


@dataclass
class AnimationCandidate:
    candidate_id: str
    direction: str
    frames: list[str]
    mean_alpha_similarity: float
    certification: CertificationState = CertificationState.CANDIDATE

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["certification"] = self.certification.value
        return out


@dataclass
class SheetAnalysis:
    schema: str
    source: SourceRecord
    grid: GridSpec
    cells: list[CellRecord]
    seams: list[SeamRecord]
    assemblies: list[AssemblyCandidate]
    animations: list[AnimationCandidate]
    duplicate_groups: dict[str, Any]
    metadata_evidence: list[dict[str, Any]]
    warnings: list[str]
    analyzer: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source": self.source.to_dict(),
            "grid": self.grid.to_dict(),
            "cells": [x.to_dict() for x in self.cells],
            "seams": [x.to_dict() for x in self.seams],
            "assemblies": [x.to_dict() for x in self.assemblies],
            "animations": [x.to_dict() for x in self.animations],
            "duplicateGroups": self.duplicate_groups,
            "metadataEvidence": self.metadata_evidence,
            "warnings": self.warnings,
            "analyzer": self.analyzer,
        }


@dataclass
class PrefabPlacement:
    x: int
    y: int
    role: str
    asset_id: str | None = None
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrefabRecipe:
    schema: str
    prefab_id: str
    prefab_type: str
    footprint: list[int]
    placements: list[PrefabPlacement]
    unresolved_roles: list[str]
    ready: bool
    certification: CertificationState = CertificationState.CANDIDATE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "prefabId": self.prefab_id,
            "prefabType": self.prefab_type,
            "footprint": self.footprint,
            "placements": [x.to_dict() for x in self.placements],
            "unresolvedRoles": self.unresolved_roles,
            "ready": self.ready,
            "certification": self.certification.value,
            "metadata": self.metadata,
        }
