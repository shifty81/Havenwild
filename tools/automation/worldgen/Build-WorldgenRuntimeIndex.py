#!/usr/bin/env python3
"""Rebuild the v0.4 worldgen runtime index from existing v0.3 scene/asset data.

This script is intentionally dependency-free. It validates that all input files exist,
then tells the developer to run scripts/Validate-WorldgenRuntimeIndex.py.
The generated v0.4 package included in this overlay was produced by the same index model.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "content/worldgen/packs/worldgen_home_island_v0_4.json"

def main() -> int:
    if not PACK.exists():
        print(f"Missing {PACK.relative_to(ROOT)}. Apply the v0.4 overlay first.")
        return 1
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    required = [
        pack["masterManifest"], pack["runtimeBindings"], pack["runtimeIndex"],
        pack["runtimeLoadOrder"], pack["assetLookup"], pack["objectFootprintRegistry"],
        pack["transitionRegistry"], pack["navigationGraph"], pack["collisionInteractionOverlay"],
        pack["cameraCompositionProfile"], pack["validationProfile"],
    ] + pack.get("sceneFiles", [])
    missing = [rel for rel in required if not (ROOT / rel).exists()]
    if missing:
        print("Worldgen runtime index inputs missing:")
        for rel in missing:
            print(f"  - {rel}")
        return 1
    print("Worldgen runtime index v0.4 is present and ready for validation.")
    print("Run: python scripts/Validate-WorldgenRuntimeIndex.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
