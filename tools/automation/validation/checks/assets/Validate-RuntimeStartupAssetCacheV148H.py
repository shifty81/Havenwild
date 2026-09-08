#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "cache": ROOT / "crates/haven_assets/src/runtime_asset_cache.rs",
    "assets": ROOT / "crates/haven_game/src/runtime_assets.rs",
    "main": ROOT / "crates/haven_game/src/main.rs",
    "policy": ROOT / "content/asset_packs/runtime_startup_cache_policy_v1.json",
}
errors = []
for label, path in required.items():
    if not path.is_file():
        errors.append(f"missing {label}: {path.relative_to(ROOT)}")

if not errors:
    cache = required["cache"].read_text(encoding="utf-8")
    assets = required["assets"].read_text(encoding="utf-8")
    main = required["main"].read_text(encoding="utf-8")
    policy = json.loads(required["policy"].read_text(encoding="utf-8"))
    checks = {
        "startup discovery": "RuntimeAssetSession::discover" in assets,
        "stable source cache": "StableAssetSourceCache" in cache,
        "semantic source resolution": "resolve_source(" in cache and "semantic_path" in assets,
        "production default": "load_project_asset_packs(project_root, false)" in cache,
        "legacy diagnostics": "using legacy path" in assets,
        "session retained": "asset_session:" in main,
        "category neutral policy": len(policy.get("consumers", [])) >= 8,
    }
    errors.extend(name for name, passed in checks.items() if not passed)

if errors:
    print("Pass 148H runtime startup/cache validation FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("Pass 148H runtime startup discovery and stable asset cache validation passed")
