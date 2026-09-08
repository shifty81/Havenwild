#!/usr/bin/env python3
"""Generate runtime caches for any compatible Universal LPC sheet definition."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = ROOT / "tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py"
RECIPE_ROOT = ROOT / "WORKSPACE/generated/lpc/character_component_recipes"


def load_builder():
    spec = importlib.util.spec_from_file_location("havenwild_ulpc_cache_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Universal LPC runtime cache builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("definition", help="path relative to sheet_definitions")
    parser.add_argument("--body", default="male", choices=("male", "female", "muscular", "pregnant", "teen", "child"))
    parser.add_argument("--id", dest="component_id")
    parser.add_argument("--animations", nargs="*", default=None)
    args = parser.parse_args()

    builder = load_builder()
    definition = Path(args.definition).as_posix().lstrip("/")
    if ".." in Path(definition).parts:
        raise SystemExit("definition path may not escape sheet_definitions")
    component_id = safe_id(args.component_id or f"dynamic_{args.body}_{Path(definition).stem}")
    available = builder.animation_paths_for_definition(definition, args.body)
    requested = set(args.animations or builder.ANIMATION_FAMILIES)
    selected = {key: value for key, value in available.items() if key in requested}
    if "walk" not in selected and "walk" in available:
        selected["walk"] = available["walk"]
    if not selected:
        raise SystemExit(f"no compatible source animations for {definition} on {args.body}")
    outputs, geometry, provenance = builder.build_component(component_id, selected)
    recipe = {
        "schema": "havenwild.universal_lpc.runtime_component_recipe.v167z40",
        "id": component_id,
        "definition": definition,
        "body": args.body,
        "outputs": outputs,
        "geometry": geometry,
        "sourceProvenance": provenance,
        "omittedAnimations": sorted(set(builder.ANIMATION_FAMILIES) - set(outputs)),
        "compatibility": "content/characters/lpc_character_compatibility_matrix_v0_1.json",
    }
    RECIPE_ROOT.mkdir(parents=True, exist_ok=True)
    recipe_path = RECIPE_ROOT / f"{component_id}.json"
    recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    print(recipe_path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
