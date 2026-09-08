#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "bindings": ROOT / "crates/haven_game/src/runtime_render_bindings.rs",
    "cache": ROOT / "crates/haven_game/src/runtime_texture_cache.rs",
    "assets": ROOT / "crates/haven_game/src/runtime_assets.rs",
    "pack": ROOT / "content/asset_packs/havenwild_worldgen/pack.json",
    "policy": ROOT / "content/asset_packs/stable_render_binding_policy_v1.json",
}
errors=[]
for label,path in required.items():
    if not path.is_file(): errors.append(f"missing {label}: {path.relative_to(ROOT)}")
if not errors:
    bindings=required["bindings"].read_text(encoding="utf-8")
    cache=required["cache"].read_text(encoding="utf-8")
    assets=required["assets"].read_text(encoding="utf-8")
    pack=json.loads(required["pack"].read_text(encoding="utf-8"))
    policy=json.loads(required["policy"].read_text(encoding="utf-8"))
    semantics={a.get("semantic_id") for a in pack.get("assets",[])}
    checks={
      "stable render role registry":"StableRenderBindingRegistry" in bindings,
      "stable refs retained":"Option<StableAssetRef>" in bindings,
      "transition semantic provider":"terrain.transition.atlas" in semantics,
      "world paint semantic provider":"terrain.world_paint.compatibility" in semantics,
      "transition semantic load":'"terrain.transition.atlas"' in assets and ".load_semantic(" in assets,
      "world paint semantic load":'"terrain.world_paint.compatibility"' in assets,
      "cache exposes resolved ref":"pub(crate) fn resolved_ref" in cache,
      "fallbacks explicit":policy.get("rules",{}).get("legacy_paths_are_explicit_fallbacks") is True,
      "seven migrated roles":len(policy.get("migrated_roles",[])) >= 7,
    }
    errors.extend(name for name,ok in checks.items() if not ok)
if errors:
    print("Pass 148J stable render binding validation FAILED")
    for e in errors: print(f"- {e}")
    raise SystemExit(1)
print("Pass 148J stable render bindings validation passed")
