from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
generator = (ROOT / "tools/automation/characters/Build-LpcPlayerAtlas.py").read_text(encoding="utf-8")
runtime = (ROOT / "crates/haven_game/src/character_runtime_compositor.rs").read_text(encoding="utf-8")

checks = {
    "repository inventory output": "lpc_character_repository_inventory_v0_1.json" in generator and "build_repository_inventory" in generator,
    "all PNG animation inventory": 'SOURCE_ROOT.rglob("*.png")' in generator,
    "authored idle discovery": "animation_candidates" in generator and '"Idle.png"' in generator and '"Stand.png"' in generator,
    "explicit generated neutral provenance": "generated_neutral_from_walk" in generator and "componentAnimationProvenance" in generator,
    "neutral walk frame selection": "neutral_walk_column" in generator,
    "separate idle and walk outputs": 'f"havenwild_player_{group_id}_idle_64.png"' in generator and 'f"havenwild_player_{group_id}_walk_64.png"' in generator,
    "runtime animation kind": "enum CharacterAnimationKind" in runtime and 'Self::Idle => "idle"' in runtime,
    "runtime idle texture": "idle_texture: Option<Texture2D>" in runtime,
    "runtime chooses idle while stopped": "layer.idle_texture.as_ref().unwrap_or(&layer.walk_texture)" in runtime,
    "idle and walk path test": "generated_idle_paths_are_distinct_from_walk_paths" in runtime,
}

missing = [name for name, ok in checks.items() if not ok]
if missing:
    print("Pass 149J27 FAILED")
    for name in missing:
        print(f"- missing {name}")
    raise SystemExit(1)
print("Pass 149J27 character repository inventory and real-idle lane validated")
