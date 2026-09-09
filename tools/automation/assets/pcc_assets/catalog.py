from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import ProjectAdapter
from .sheet import analyze_sheet
from .tiled import inspect_tiled


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_asset_root(
    root: Path,
    adapter: ProjectAdapter,
    cell_width: int | None = None,
    cell_height: int | None = None,
    max_files: int | None = None,
    progress=None,
) -> dict[str, Any]:
    root = root.resolve()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if max_files is not None:
        files = files[:max_files]

    tiled_by_image_name: dict[str, list[dict[str, Any]]] = {}
    tiled_records = []
    errors = []

    metadata_candidates = [p for p in files if p.suffix.lower() in {".tsx", ".tmx"}]
    for idx, p in enumerate(metadata_candidates, 1):
        if progress and (idx == 1 or idx % 25 == 0 or idx == len(metadata_candidates)):
            progress("metadata", idx, len(metadata_candidates), p)
        try:
            ev = inspect_tiled(p)
            ev["relativePath"] = _rel(root, p)
            tiled_records.append(ev)
            if p.suffix.lower() == ".tsx":
                image_source = (ev.get("image") or {}).get("source")
                if image_source:
                    tiled_by_image_name.setdefault(Path(image_source).name.lower(), []).append(ev)
        except Exception as exc:
            errors.append({"path": _rel(root, p), "error": str(exc)})

    sheets = []
    png_candidates = [p for p in files if p.suffix.lower() == ".png"]
    for idx, p in enumerate(png_candidates, 1):
        if progress and (idx == 1 or idx % 25 == 0 or idx == len(png_candidates)):
            progress("sheet", idx, len(png_candidates), p)
        try:
            metadata = tiled_by_image_name.get(p.name.lower(), [])
            analysis = analyze_sheet(
                p, adapter,
                cell_width=cell_width,
                cell_height=cell_height,
                metadata_evidence=[
                    {
                        "kind": "tiled_tileset",
                        "path": x["relativePath"],
                        "summary": x["summary"],
                        "certification": x["certification"],
                    }
                    for x in metadata
                ],
            ).to_dict()
            analysis["source"]["relativePath"] = _rel(root, p)
            sheets.append(analysis)
        except Exception as exc:
            errors.append({"path": _rel(root, p), "error": str(exc)})

    assemblies = []
    for sheet in sheets:
        source_rel = sheet["source"]["relativePath"]
        for asm in sheet["assemblies"]:
            assemblies.append({
                "assetId": f"{source_rel}#{asm['assembly_id']}",
                "source": source_rel,
                **asm,
            })

    return {
        "schema": "pcc.asset.catalog.v1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "root": root.as_posix(),
        "adapter": adapter.name,
        "policy": {
            "automaticRuntimeCertification": False,
            "semanticsInferredFromPixels": False,
            "sourcePixelsAreImmutableAuthority": True,
        },
        "summary": {
            "pngSheetCount": len(sheets),
            "tiledMetadataCount": len(tiled_records),
            "assemblyCandidateCount": len(assemblies),
            "errorCount": len(errors),
        },
        "sheets": sheets,
        "tiled": tiled_records,
        "assemblyIndex": assemblies,
        "errors": errors,
    }


def write_catalog(path: Path, catalog: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
