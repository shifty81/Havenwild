#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "resource_registry": ROOT / "crates/haven_assets/src/semantic_resource_bindings.rs",
    "stamp_registry": ROOT / "crates/haven_assets/src/stamp_registry.rs",
    "runtime_assets": ROOT / "crates/haven_game/src/runtime_assets.rs",
    "objects_pack": ROOT / "content/asset_packs/havenwild_objects/pack.json",
    "characters_pack": ROOT / "content/asset_packs/havenwild_characters/pack.json",
    "audio_pack": ROOT / "content/asset_packs/havenwild_audio/pack.json",
    "interface_pack": ROOT / "content/asset_packs/havenwild_interface/pack.json",
    "policy": ROOT / "content/asset_packs/semantic_resource_provider_policy_v1.json",
}
errors=[]
for label,path in required.items():
    if not path.is_file(): errors.append(f"missing {label}: {path.relative_to(ROOT)}")
if not errors:
    registry=required["resource_registry"].read_text(encoding="utf-8")
    stamp=required["stamp_registry"].read_text(encoding="utf-8")
    runtime=required["runtime_assets"].read_text(encoding="utf-8")
    policy=json.loads(required["policy"].read_text(encoding="utf-8"))
    semantics=set()
    for key in ("objects_pack","characters_pack","audio_pack","interface_pack"):
        pack=json.loads(required[key].read_text(encoding="utf-8"))
        semantics.update(a.get("semantic_id") for a in pack.get("assets",[]))
    required_semantics=set(policy.get("initialResources",[]))
    checks={
      "generic semantic resource registry":"SemanticResourceRegistry" in registry,
      "stable resource binding":"StableAssetRef" in registry and "ResolvedAssetSource" not in registry,
      "production session resolution":"session.resolve_source" in registry,
      "diagnostic fallback":"No stable non-texture provider" in registry,
      "semantic stamp manifest":"stamp.catalog.ponds" in semantics,
      "semantic stamp sheet":"stamp.sheet.ponds" in semantics,
      "animation contract":"animation.contract.default" in semantics,
      "audio contract":"audio.contract.events" in semantics,
      "music contract":"music.contract.events" in semantics,
      "ui generation contract":"ui.contract.generation" in semantics,
      "ui save contract":"ui.contract.save_slots" in semantics,
      "all policy resources mounted":required_semantics.issubset(semantics),
      "stamp registry accepts manifest provider":"load_from_manifest_path" in stamp,
      "runtime uses semantic resources":"resource_bindings.resolve" in runtime,
      "save previews excluded":policy.get("rules",{}).get("saveOwnedPreviewsAreNotAssetPackResources") is True,
      "diagnostic previews excluded":policy.get("rules",{}).get("generatedDiagnosticPreviewsAreNotProductionResources") is True,
    }
    errors.extend(name for name,ok in checks.items() if not ok)
if errors:
    print("Pass 148K semantic resource provider validation FAILED")
    for error in errors: print(f"- {error}")
    raise SystemExit(1)
print("Pass 148K semantic resource provider validation passed")
