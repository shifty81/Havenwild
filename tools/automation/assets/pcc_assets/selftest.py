from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .adapters import HAVENWILD
from .catalog import scan_asset_root, write_catalog
from .pngio import Image, encode_png
from .prefab import generate_house_prefab
from .sheet import analyze_sheet
from .tiled import inspect_tsx
from .validate import validate_catalog


def _synthetic_sheet(path: Path) -> None:
    w, h = 96, 64  # 3x2 cells at 32px.
    rgba = bytearray(w * h * 4)

    def fill(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]):
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * w + x) * 4
                rgba[i:i+4] = bytes(color)

    # A source-native 2x2 connected object spanning four cells.
    fill(8, 8, 56, 56, (80, 120, 90, 255))
    # Standalone object in c2r0.
    fill(72, 8, 88, 24, (150, 80, 40, 255))
    encode_png(path, Image(w, h, bytes(rgba)))


def _synthetic_tsx(path: Path) -> None:
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.2" name="Synthetic" tilewidth="32" tileheight="32" tilecount="6" columns="3">
 <image source="sheet.png" width="96" height="64"/>
 <wangsets>
  <wangset name="Terrain" type="corner" tile="-1">
   <wangcolor name="Ground" color="#ff00ff" tile="0" probability="1"/>
   <wangtile tileid="0" wangid="1,1,1,1,1,1,1,1"/>
  </wangset>
 </wangsets>
 <tile id="0">
  <properties><property name="kind" value="ground"/></properties>
  <objectgroup><object id="1" x="0" y="16" width="32" height="16"/></objectgroup>
  <animation><frame tileid="0" duration="100"/><frame tileid="1" duration="100"/></animation>
 </tile>
</tileset>
""",
        encoding="utf-8",
    )


def run_selftest() -> dict:
    with tempfile.TemporaryDirectory(prefix="pcc-assets-selftest-") as td:
        root = Path(td)
        sheet = root / "sheet.png"
        tsx = root / "sheet.tsx"
        _synthetic_sheet(sheet)
        _synthetic_tsx(tsx)

        analysis = analyze_sheet(sheet, HAVENWILD)
        assert analysis.grid.cell_width == 32
        assert analysis.grid.columns == 3
        assert any(len(a.members) >= 4 for a in analysis.assemblies), analysis.to_dict()

        tiled = inspect_tsx(tsx)
        assert tiled["summary"]["wangSetCount"] == 1
        assert tiled["summary"]["wangAssignmentCount"] == 1
        assert tiled["summary"]["collisionTileCount"] == 1
        assert tiled["summary"]["animatedTileCount"] == 1

        catalog = scan_asset_root(root, HAVENWILD)
        assert catalog["summary"]["pngSheetCount"] == 1
        assert catalog["summary"]["tiledMetadataCount"] == 1
        assert not validate_catalog(catalog)

        # Writer contract: compact and full catalogs must each be exactly one
        # JSON document and must survive a strict json.loads round trip.
        compact_path = root / "catalog-compact.json"
        full_path = root / "catalog-full.json"
        write_catalog(compact_path, catalog, detail="compact")
        write_catalog(full_path, catalog, detail="full")
        compact_payload = json.loads(compact_path.read_text(encoding="utf-8"))
        full_payload = json.loads(full_path.read_text(encoding="utf-8"))
        assert compact_payload["storage"]["mode"] == "compact"
        assert full_payload["summary"] == catalog["summary"]
        assert not compact_path.with_name(compact_path.name + ".tmp").exists()
        assert not full_path.with_name(full_path.name + ".tmp").exists()

        role_map = {
            "schema": "pcc.asset.role_map.v1",
            "roles": {
                "building.wall.corner.nw": "a",
                "building.wall.corner.ne": "b",
                "building.wall.corner.sw": "c",
                "building.wall.corner.se": "d",
                "building.wall.north": "n",
                "building.wall.south": "s",
                "building.wall.west": "w",
                "building.wall.east": "e",
                "building.opening.door.south": "door",
            },
        }
        prefab = generate_house_prefab(7, 7, role_map)
        assert prefab.ready
        assert not prefab.unresolved_roles

        unresolved = generate_house_prefab(7, 7, {"schema": "pcc.asset.role_map.v1", "roles": {}})
        assert not unresolved.ready
        assert unresolved.unresolved_roles

        return {
            "schema": "pcc.asset.selftest.v1",
            "status": "PASS",
            "checks": {
                "pngDecodeEncode": True,
                "grid32": True,
                "multiCellAssembly": True,
                "tsxWang": True,
                "tsxCollision": True,
                "tsxAnimation": True,
                "catalogScan": True,
                "catalogValidation": True,
                "catalogAtomicWrite": True,
                "catalogStrictJsonRoundTrip": True,
                "prefabResolved": True,
                "prefabUnresolvedSafety": True,
            },
        }
