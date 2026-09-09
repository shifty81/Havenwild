from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CertificationState, PrefabPlacement, PrefabRecipe


ALLOWED_CERTIFICATIONS = {
    CertificationState.METADATA_VERIFIED.value,
    CertificationState.EXAMPLE_VERIFIED.value,
    CertificationState.RUNTIME_CERTIFIED.value,
}


def load_role_map(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"schema": "pcc.asset.role_map.v1", "roles": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "pcc.asset.role_map.v1":
        raise ValueError("unexpected role-map schema")
    return data


def _resolve(role_map: dict[str, Any], role: str) -> str | None:
    value = role_map.get("roles", {}).get(role)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        certification = value.get("certification")
        if certification and certification not in ALLOWED_CERTIFICATIONS:
            return None
        return value.get("assetId")
    return None


def generate_house_prefab(
    width: int,
    height: int,
    role_map: dict[str, Any],
    prefab_id: str = "generated-house",
    door_x: int | None = None,
) -> PrefabRecipe:
    if width < 5 or height < 5:
        raise ValueError("house footprint must be at least 5x5")
    if door_x is None:
        door_x = width // 2
    if door_x <= 0 or door_x >= width - 1:
        raise ValueError("door must not occupy a corner")

    placements: list[PrefabPlacement] = []

    def add(x: int, y: int, role: str, required: bool = True) -> None:
        placements.append(PrefabPlacement(
            x=x, y=y, role=role, asset_id=_resolve(role_map, role), required=required
        ))

    # Perimeter grammar. Semantics are explicit; source art is never invented.
    add(0, 0, "building.wall.corner.nw")
    add(width - 1, 0, "building.wall.corner.ne")
    add(0, height - 1, "building.wall.corner.sw")
    add(width - 1, height - 1, "building.wall.corner.se")

    for x in range(1, width - 1):
        add(x, 0, "building.wall.north")
        if x == door_x:
            add(x, height - 1, "building.opening.door.south")
        else:
            add(x, height - 1, "building.wall.south")

    for y in range(1, height - 1):
        add(0, y, "building.wall.west")
        add(width - 1, y, "building.wall.east")

    # Roof is represented as semantic slots in a separate logical layer.
    for x in range(width):
        add(x, -1, "building.roof.south_or_gable", required=False)

    unresolved = sorted({
        p.role for p in placements
        if p.required and not p.asset_id
    })
    ready = not unresolved
    certification = (
        CertificationState.METADATA_VERIFIED
        if ready else CertificationState.CANDIDATE
    )

    return PrefabRecipe(
        schema="pcc.asset.prefab_recipe.v1",
        prefab_id=prefab_id,
        prefab_type="house",
        footprint=[width, height],
        placements=placements,
        unresolved_roles=unresolved,
        ready=ready,
        certification=certification,
        metadata={
            "generator": "pcc-assets.house.v1",
            "door": {"side": "south", "x": door_x},
            "sourceArtInvented": False,
            "interiorFootprintAuthority": "project_adapter_or_editor",
        },
    )


def extract_source_native_prefabs(catalog: dict[str, Any]) -> dict[str, Any]:
    prefabs = []
    for asm in catalog.get("assemblyIndex", []):
        prefabs.append({
            "schema": "pcc.asset.prefab_recipe.v1",
            "prefabId": asm["assetId"],
            "prefabType": "source_native_assembly",
            "footprint": asm["footprint"],
            "source": asm["source"],
            "sourceRectPx": asm["source_rect_px"],
            "members": asm["members"],
            "anchor": None,
            "semanticRole": None,
            "ready": False,
            "certification": CertificationState.CANDIDATE.value,
            "unresolved": ["anchor", "semanticRole", "independentPlacementEvidence"],
            "evidence": asm.get("evidence", []),
        })
    return {
        "schema": "pcc.asset.prefab_catalog.v1",
        "sourceCatalog": catalog.get("schema"),
        "prefabs": prefabs,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
