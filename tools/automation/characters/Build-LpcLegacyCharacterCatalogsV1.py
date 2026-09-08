#!/usr/bin/env python3
"""Rebuild checked-in ElizaWy/LPC character catalogs without replacing runtime atlases.

Normal lean source rollups omit these large derived JSON catalogs. They are
reconstructed from the pinned `assets/source/licensed/lpc_revised` mount during
bootstrap. Runtime character images remain owned by the newer Universal LPC
cache builder and are deliberately untouched here.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/automation/characters/Build-LpcPlayerAtlas.py"
sys.path.insert(0, str(ROOT / "tools" / "automation"))
from common.atomic_io import atomic_write_json


def load_generator():
    spec = importlib.util.spec_from_file_location("havenwild_lpc_player_catalog_source", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load catalog generator: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    generator = load_generator()
    files = generator.walk_files()
    groups = generator.discovered_groups()
    selected_sources = {source for paths in groups.values() for source in paths}

    outputs = (
        (generator.SHEET_CATALOG, generator.build_sheet_catalog(files, selected_sources)),
        (generator.ANIMATION_CATALOG, generator.build_animation_catalog()),
        (generator.CHARACTER_INVENTORY, generator.build_repository_inventory()),
        (generator.PRODUCTION_CATALOG, generator.build_production_catalog()),
    )
    for path, payload in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(path, payload)
        print(f"Wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
