from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .models import CertificationState
from .provenance import sha256_file


def _properties(node: ET.Element | None) -> dict[str, Any]:
    if node is None:
        return {}
    out: dict[str, Any] = {}
    for prop in node.findall("property"):
        name = prop.get("name")
        if not name:
            continue
        value = prop.get("value")
        if value is None:
            value = prop.text or ""
        typ = prop.get("type", "string")
        if typ == "bool":
            value = str(value).lower() == "true"
        elif typ in {"int", "integer"}:
            try:
                value = int(value)
            except ValueError:
                pass
        elif typ == "float":
            try:
                value = float(value)
            except ValueError:
                pass
        out[name] = value
    return out


def inspect_tsx(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    if root.tag != "tileset":
        raise ValueError(f"not a TSX tileset: {path}")
    image = root.find("image")
    wangsets = []
    for ws in root.findall("./wangsets/wangset"):
        wangsets.append({
            "name": ws.get("name"),
            "type": ws.get("type"),
            "tile": ws.get("tile"),
            "properties": _properties(ws.find("properties")),
            "colors": [
                {
                    "name": c.get("name"),
                    "color": c.get("color"),
                    "tile": c.get("tile"),
                    "probability": c.get("probability"),
                }
                for c in ws.findall("wangcolor")
            ],
            "assignments": [
                {
                    "tileId": int(wt.get("tileid", "0")),
                    "wangId": wt.get("wangid", ""),
                }
                for wt in ws.findall("wangtile")
            ],
        })

    tiles = []
    for tile in root.findall("tile"):
        animation = tile.find("animation")
        objectgroup = tile.find("objectgroup")
        collision = []
        if objectgroup is not None:
            for obj in objectgroup.findall("object"):
                collision.append({
                    "id": obj.get("id"),
                    "x": obj.get("x"),
                    "y": obj.get("y"),
                    "width": obj.get("width"),
                    "height": obj.get("height"),
                    "ellipse": obj.find("ellipse") is not None,
                    "polygon": obj.find("polygon").get("points") if obj.find("polygon") is not None else None,
                    "polyline": obj.find("polyline").get("points") if obj.find("polyline") is not None else None,
                    "properties": _properties(obj.find("properties")),
                })
        tiles.append({
            "id": int(tile.get("id", "0")),
            "class": tile.get("class") or tile.get("type"),
            "properties": _properties(tile.find("properties")),
            "animation": [
                {
                    "tileId": int(frame.get("tileid", "0")),
                    "durationMs": int(frame.get("duration", "0")),
                }
                for frame in animation.findall("frame")
            ] if animation is not None else [],
            "collision": collision,
        })

    return {
        "schema": "pcc.asset.tiled_tileset_evidence.v1",
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "name": root.get("name"),
        "tileWidth": int(root.get("tilewidth", "0") or 0),
        "tileHeight": int(root.get("tileheight", "0") or 0),
        "tileCount": int(root.get("tilecount", "0") or 0),
        "columns": int(root.get("columns", "0") or 0),
        "spacing": int(root.get("spacing", "0") or 0),
        "margin": int(root.get("margin", "0") or 0),
        "image": {
            "source": image.get("source") if image is not None else None,
            "width": int(image.get("width", "0") or 0) if image is not None else None,
            "height": int(image.get("height", "0") or 0) if image is not None else None,
        },
        "properties": _properties(root.find("properties")),
        "wangSets": wangsets,
        "tiles": tiles,
        "summary": {
            "wangSetCount": len(wangsets),
            "wangAssignmentCount": sum(len(x["assignments"]) for x in wangsets),
            "animatedTileCount": sum(1 for x in tiles if x["animation"]),
            "collisionTileCount": sum(1 for x in tiles if x["collision"]),
            "propertyTileCount": sum(1 for x in tiles if x["properties"]),
        },
        "certification": CertificationState.METADATA_VERIFIED.value,
    }


def inspect_tmx(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    if root.tag != "map":
        raise ValueError(f"not a TMX map: {path}")
    tilesets = []
    for ts in root.findall("tileset"):
        tilesets.append({
            "firstGid": int(ts.get("firstgid", "0") or 0),
            "source": ts.get("source"),
            "name": ts.get("name"),
            "tileWidth": int(ts.get("tilewidth", "0") or 0),
            "tileHeight": int(ts.get("tileheight", "0") or 0),
        })
    layers = []
    for child in list(root):
        if child.tag in {"layer", "objectgroup", "imagelayer", "group"}:
            layers.append({
                "type": child.tag,
                "name": child.get("name"),
                "class": child.get("class") or child.get("type"),
                "properties": _properties(child.find("properties")),
            })
    return {
        "schema": "pcc.asset.tiled_map_evidence.v1",
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "orientation": root.get("orientation"),
        "renderOrder": root.get("renderorder"),
        "width": int(root.get("width", "0") or 0),
        "height": int(root.get("height", "0") or 0),
        "tileWidth": int(root.get("tilewidth", "0") or 0),
        "tileHeight": int(root.get("tileheight", "0") or 0),
        "tilesets": tilesets,
        "layers": layers,
        "properties": _properties(root.find("properties")),
        "certification": CertificationState.METADATA_VERIFIED.value,
    }


def inspect_tiled(path: Path) -> dict[str, Any]:
    ext = path.suffix.lower()
    if ext == ".tsx":
        return inspect_tsx(path)
    if ext == ".tmx":
        return inspect_tmx(path)
    raise ValueError(f"unsupported Tiled metadata file: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
