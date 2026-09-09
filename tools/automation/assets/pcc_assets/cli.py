from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import get_adapter
from .catalog import scan_asset_root, write_catalog
from .prefab import (
    extract_source_native_prefabs,
    generate_house_prefab,
    load_role_map,
    write_json as write_prefab_json,
)
from .selftest import run_selftest
from .migration import inventory_existing_tools
from .sheet import analyze_sheet
from .tiled import inspect_tiled, write_json as write_tiled_json
from .validate import validate_catalog


def _write(path: Path | None, payload: dict) -> None:
    text = json.dumps(payload, indent=2) + "\n"
    if path is None:
        print(text, end="")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pcc-assets",
        description="Universal Python asset intake/analyzer/prefab subsystem",
    )
    p.add_argument("--adapter", default="havenwild", choices=["havenwild", "generic"])
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("self-test", help="run the subsystem's deterministic self-test")
    s.add_argument("--output", type=Path)

    s = sub.add_parser("analyze-sheet", help="analyze one PNG sheet")
    s.add_argument("sheet", type=Path)
    s.add_argument("--cell-width", type=int)
    s.add_argument("--cell-height", type=int)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("scan", help="scan a folder into a canonical asset catalog")
    s.add_argument("root", type=Path)
    s.add_argument("--cell-width", type=int)
    s.add_argument("--cell-height", type=int)
    s.add_argument("--max-files", type=int)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("inspect-tiled", help="parse TSX/TMX metadata evidence")
    s.add_argument("path", type=Path)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("extract-prefabs", help="turn detected source assemblies into prefab candidates")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("generate-house", help="generate a semantic house prefab recipe")
    s.add_argument("--width", type=int, default=7)
    s.add_argument("--height", type=int, default=7)
    s.add_argument("--door-x", type=int)
    s.add_argument("--prefab-id", default="generated-house")
    s.add_argument("--role-map", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("validate-catalog", help="validate a canonical asset catalog")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("inventory-tools", help="inventory existing automation for PCC asset normalization")
    s.add_argument("repo_root", type=Path)
    s.add_argument("--output", type=Path, required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    adapter = get_adapter(args.adapter)

    if args.command == "self-test":
        result = run_selftest()
        _write(args.output, result)
        return 0

    if args.command == "analyze-sheet":
        if bool(args.cell_width) != bool(args.cell_height):
            raise SystemExit("--cell-width and --cell-height must be supplied together")
        result = analyze_sheet(
            args.sheet,
            adapter,
            cell_width=args.cell_width,
            cell_height=args.cell_height,
        ).to_dict()
        _write(args.output, result)
        return 0

    if args.command == "scan":
        if bool(args.cell_width) != bool(args.cell_height):
            raise SystemExit("--cell-width and --cell-height must be supplied together")
        def progress(kind, index, total, path):
            print(f"[{kind.upper()}] {index}/{total} {path}")

        catalog = scan_asset_root(
            args.root,
            adapter,
            cell_width=args.cell_width,
            cell_height=args.cell_height,
            max_files=args.max_files,
            progress=progress,
        )
        write_catalog(args.output, catalog)
        print(
            f"Sheets={catalog['summary']['pngSheetCount']} "
            f"Tiled={catalog['summary']['tiledMetadataCount']} "
            f"Assemblies={catalog['summary']['assemblyCandidateCount']} "
            f"Errors={catalog['summary']['errorCount']}"
        )
        return 0 if not catalog["errors"] else 2

    if args.command == "inspect-tiled":
        result = inspect_tiled(args.path)
        if args.output:
            write_tiled_json(args.output, result)
            print(args.output)
        else:
            _write(None, result)
        return 0

    if args.command == "extract-prefabs":
        result = extract_source_native_prefabs(_load_json(args.catalog))
        write_prefab_json(args.output, result)
        print(args.output)
        return 0

    if args.command == "generate-house":
        role_map = load_role_map(args.role_map)
        result = generate_house_prefab(
            args.width,
            args.height,
            role_map,
            prefab_id=args.prefab_id,
            door_x=args.door_x,
        ).to_dict()
        write_prefab_json(args.output, result)
        print(args.output)
        if not result["ready"]:
            print("Prefab is a safe candidate only; unresolved roles:")
            for role in result["unresolvedRoles"]:
                print(f"  - {role}")
        return 0

    if args.command == "validate-catalog":
        problems = validate_catalog(_load_json(args.catalog))
        result = {
            "schema": "pcc.asset.catalog_validation.v1",
            "status": "PASS" if not problems else "FAIL",
            "problems": problems,
        }
        _write(args.output, result)
        return 0 if not problems else 3

    if args.command == "inventory-tools":
        result = inventory_existing_tools(args.repo_root)
        _write(args.output, result)
        print(
            f"Existing automation tools inventoried: "
            f"{result['summary']['toolCount']}"
        )
        return 0

    raise SystemExit(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
