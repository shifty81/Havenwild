from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .adapters import get_adapter
from .authority import (
    build_certification_queue,
    build_derive_plan,
    build_prefab_library,
    build_promotion_plan,
)
from .catalog import PROFILE_NAMES, scan_asset_root, write_catalog
from .intake import build_source_manifest
from .migration import inventory_existing_tools
from .normalization import build_normalization_plan, select_normalization_batch
from .prefab import (
    extract_source_native_prefabs,
    generate_house_prefab,
    load_role_map,
    write_json as write_prefab_json,
)
from .selftest import run_selftest
from .services import service_registry
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
        description="Universal Python asset intake/analyzer/prefab/authority subsystem",
    )
    p.add_argument("--adapter", default="havenwild", choices=["havenwild", "generic"])
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("self-test", help="run deterministic subsystem self-test")
    s.add_argument("--output", type=Path)

    s = sub.add_parser("services", help="show canonical universal asset services")
    s.add_argument("--output", type=Path)

    s = sub.add_parser("source-manifest", help="inventory folder/file/ZIP without modifying it")
    s.add_argument("source", type=Path)
    s.add_argument("--source-id")
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("analyze-sheet", help="deep-analyze one PNG sheet")
    s.add_argument("sheet", type=Path)
    s.add_argument("--cell-width", type=int)
    s.add_argument("--cell-height", type=int)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("scan", help="staged scalable scan into canonical asset catalog")
    s.add_argument("root", type=Path)
    s.add_argument("--profile", choices=PROFILE_NAMES, default="smart")
    s.add_argument("--workers", type=int)
    s.add_argument("--max-deep", type=int)
    s.add_argument("--cell-width", type=int)
    s.add_argument("--cell-height", type=int)
    s.add_argument("--max-files", type=int)
    s.add_argument("--cache", type=Path)
    s.add_argument("--checkpoint", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("inspect-tiled", help="parse TSX/TMX metadata evidence")
    s.add_argument("path", type=Path)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("extract-prefabs", help="turn detected source assemblies into prefab candidates")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("prefab-library", help="build source-native + semantic prefab library")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("generate-house", help="generate semantic house prefab recipe")
    s.add_argument("--width", type=int, default=7)
    s.add_argument("--height", type=int, default=7)
    s.add_argument("--door-x", type=int)
    s.add_argument("--prefab-id", default="generated-house")
    s.add_argument("--role-map", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("certification-queue", help="build review queue; never auto-certifies")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("derive-plan", help="plan derived outputs with lineage requirements")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("promotion-plan", help="plan runtime promotion from certified assets only")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("validate-catalog", help="validate canonical asset catalog")
    s.add_argument("catalog", type=Path)
    s.add_argument("--output", type=Path)

    s = sub.add_parser("inventory-tools", help="inventory existing automation for normalization")
    s.add_argument("repo_root", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("normalization-plan", help="group legacy inventory into parity-safe batches")
    s.add_argument("inventory", type=Path)
    s.add_argument("--output", type=Path, required=True)

    s = sub.add_parser("normalization-batch", help="select one normalization target batch")
    s.add_argument("inventory", type=Path)
    s.add_argument("--target", required=True)
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--output", type=Path, required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    adapter = get_adapter(args.adapter)

    if args.command == "self-test":
        _write(args.output, run_selftest())
        return 0

    if args.command == "services":
        _write(args.output, service_registry())
        return 0

    if args.command == "source-manifest":
        _write(args.output, build_source_manifest(args.source, args.source_id))
        return 0

    if args.command == "analyze-sheet":
        if bool(args.cell_width) != bool(args.cell_height):
            raise SystemExit("--cell-width and --cell-height must be supplied together")
        _write(
            args.output,
            analyze_sheet(
                args.sheet, adapter,
                cell_width=args.cell_width, cell_height=args.cell_height,
            ).to_dict(),
        )
        return 0

    if args.command == "scan":
        if bool(args.cell_width) != bool(args.cell_height):
            raise SystemExit("--cell-width and --cell-height must be supplied together")

        phase_starts: dict[str, float] = {}
        def progress(kind, index, total, path):
            now = time.perf_counter()
            phase_starts.setdefault(kind, now)
            elapsed = max(0.001, now - phase_starts[kind])
            rate = index / elapsed
            remaining = max(0, total - index)
            eta = remaining / rate if rate > 0 else 0
            print(
                f"[{kind.upper()}] {index}/{total} "
                f"rate={rate:.1f}/s eta={eta/60:.1f}m {path}"
            )

        checkpoint = args.checkpoint or (
            args.output.parent / (args.output.stem + ".scan-progress.json")
        )
        cache = args.cache or Path(
            "artifacts/asset-intake/cache/pcc_asset_cache.sqlite"
        )
        try:
            catalog = scan_asset_root(
                args.root, adapter,
                cell_width=args.cell_width,
                cell_height=args.cell_height,
                max_files=args.max_files,
                progress=progress,
                profile=args.profile,
                workers=args.workers,
                max_deep=args.max_deep,
                cache_path=cache,
                checkpoint_path=checkpoint,
            )
        except KeyboardInterrupt:
            print()
            print("[INTERRUPTED] Completed cache work was preserved.")
            print(f"Checkpoint: {checkpoint}")
            return 130

        write_catalog(args.output, catalog)
        summary = catalog["summary"]
        print(
            f"Files={summary['discoveredFileCount']} "
            f"PNGs={summary['pngFileCount']} "
            f"Deep={summary['pngSheetCount']}/{summary['deepCandidateCount']} "
            f"Deferred={summary['deepDeferredCount']} "
            f"HashCache={summary['hashCacheHits']} "
            f"AnalysisCache={summary['analysisCacheHits']} "
            f"Assemblies={summary['assemblyCandidateCount']} "
            f"Errors={summary['errorCount']}"
        )
        print(f"Catalog: {args.output}")
        print(f"Checkpoint: {checkpoint}")
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

    if args.command == "prefab-library":
        _write(args.output, build_prefab_library(_load_json(args.catalog)))
        return 0

    if args.command == "generate-house":
        result = generate_house_prefab(
            args.width, args.height, load_role_map(args.role_map),
            prefab_id=args.prefab_id, door_x=args.door_x,
        ).to_dict()
        write_prefab_json(args.output, result)
        print(args.output)
        if not result["ready"]:
            print("Prefab is a safe candidate only; unresolved roles:")
            for role in result["unresolvedRoles"]:
                print(f"  - {role}")
        return 0

    if args.command == "certification-queue":
        _write(args.output, build_certification_queue(_load_json(args.catalog)))
        return 0

    if args.command == "derive-plan":
        _write(args.output, build_derive_plan(_load_json(args.catalog)))
        return 0

    if args.command == "promotion-plan":
        _write(args.output, build_promotion_plan(_load_json(args.catalog)))
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
        print(f"Existing automation tools inventoried: {result['summary']['toolCount']}")
        return 0

    if args.command == "normalization-plan":
        _write(args.output, build_normalization_plan(_load_json(args.inventory)))
        return 0

    if args.command == "normalization-batch":
        _write(
            args.output,
            select_normalization_batch(
                _load_json(args.inventory), args.target, args.limit
            ),
        )
        return 0

    raise SystemExit(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
