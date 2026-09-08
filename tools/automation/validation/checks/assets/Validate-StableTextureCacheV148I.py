#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "source_cache": ROOT / "crates/haven_assets/src/runtime_asset_cache.rs",
    "texture_cache": ROOT / "crates/haven_game/src/runtime_texture_cache.rs",
    "assets": ROOT / "crates/haven_game/src/runtime_assets.rs",
    "main": ROOT / "crates/haven_game/src/main.rs",
    "policy": ROOT / "content/asset_packs/runtime_texture_cache_policy_v1.json",
}
errors = []
for label, path in required.items():
    if not path.is_file():
        errors.append(f"missing {label}: {path.relative_to(ROOT)}")

if not errors:
    cache = required["texture_cache"].read_text(encoding="utf-8")
    assets = required["assets"].read_text(encoding="utf-8")
    main = required["main"].read_text(encoding="utf-8")
    policy = json.loads(required["policy"].read_text(encoding="utf-8"))
    checks = {
        "stable asset keyed cache": "HashMap<StableAssetRef, Texture2D>" in cache,
        "source path deduplication": "HashMap<PathBuf, Texture2D>" in cache,
        "stable source loading": "load_stable_source" in cache,
        "semantic cache loading": "load_semantic" in cache,
        "explicit fallback records": "LegacyTextureFallback" in cache,
        "shared texture aliases": ".load_semantic(" in assets and "StableTextureCache" in assets,
        "stamp texture deduplication": "texture_cache.load_path" in assets,
        "cache retained by game": "_texture_cache:" in main,
        "fallback diagnostics retained": "legacy_fallbacks()" in main,
        "load once policy": policy.get("rules", {}).get("load_once_per_source_path") is True,
        "stable key contract": len(policy.get("stable_reference_key", [])) == 5,
        "category neutral bindings": len(policy.get("initial_bindings", [])) >= 5,
    }
    errors.extend(name for name, passed in checks.items() if not passed)

if errors:
    print("Pass 148I stable texture cache validation FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("Pass 148I stable texture cache and renderer binding validation passed")
