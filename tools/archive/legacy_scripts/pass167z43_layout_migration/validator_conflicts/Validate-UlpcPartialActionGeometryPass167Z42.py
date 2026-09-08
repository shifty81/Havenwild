#!/usr/bin/env python3
"""Validate Pass 167Z42 partial Universal LPC action geometry handling."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("havenwild_ulpc_cache_builder_v167z42", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save_sheet(path: Path, size: tuple[int, int], rgba: tuple[int, int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, rgba).save(path)


def main() -> int:
    module = load_builder()
    assert module.REVISION == "167Z42-partial-action-geometry-compatibility-v2"

    with tempfile.TemporaryDirectory(prefix="havenwild-z42-") as temporary:
        fixture = Path(temporary)
        module.ROOT = fixture
        module.SOURCE = fixture / "source"
        module.LAYER_ROOT = fixture / "assets/generated/lpc/characters/layers"
        module.OUTPUT_ROOT = fixture / "assets/generated/lpc/characters"

        walk = module.SOURCE / "body/bodies/child/walk.png"
        partial_run = module.SOURCE / "body/bodies/child/run/base.png"
        watering = module.SOURCE / "body/bodies/child/watering.png"
        save_sheet(walk, (576, 256), (30, 120, 220, 255))
        save_sheet(partial_run, (384, 64), (220, 80, 50, 255))
        save_sheet(watering, (384, 256), (80, 200, 90, 255))

        outputs, geometry, provenance, omissions = module.build_component(
            "body_child",
            {
                "walk": [walk],
                "run": [partial_run],
                "watering": [watering],
            },
        )

        assert {"walk", "idle", "watering"}.issubset(outputs)
        assert "run" not in outputs
        assert geometry["idle"]["fallbackFrom"] == "walk"
        assert geometry["watering"]["rows"] == 4
        assert provenance["walk"] == ["body/bodies/child/walk.png"]
        assert any("body_child.run" in entry and "384, 64" in entry for entry in omissions)
        assert Path(fixture / outputs["walk"]).is_file()
        assert Path(fixture / outputs["idle"]).is_file()
        assert Path(fixture / outputs["watering"]).is_file()

        bad_walk = module.SOURCE / "body/bodies/bad/walk.png"
        save_sheet(bad_walk, (384, 64), (255, 255, 255, 255))
        try:
            module.build_component("body_bad", {"walk": [bad_walk]})
        except ValueError as error:
            assert "walk source is not runtime-compatible" in str(error)
        else:
            raise AssertionError("a partial one-row walk strip must remain a fatal body-cache error")

    source = BUILDER.read_text(encoding="utf-8")
    required_markers = [
        "partialActionGeometryPolicy",
        "action omitted",
        "expected at least {ROWS} directional rows",
        "optional_failures.extend(action_omissions)",
        "componentAnimationAvailability",
    ]
    missing = [marker for marker in required_markers if marker not in source]
    if missing:
        raise AssertionError(f"missing Z42 source markers: {missing}")

    print("Pass 167Z42 Universal LPC partial-action geometry contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
