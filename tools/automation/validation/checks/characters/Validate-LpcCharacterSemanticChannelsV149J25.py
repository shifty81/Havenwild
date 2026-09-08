from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
GEN = (ROOT / "tools/automation/characters/Build-LpcPlayerAtlas.py").read_text(encoding="utf-8")
BUILD = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")

checks = {
    "strict semantic channels": "def semantic_channel" in GEN,
    "scalp and facial hair split": 'return "scalp_hair"' in GEN and 'return "facial_hair"' in GEN,
    "modular geometry gate": "def layer_geometry_valid" in GEN,
    "torso rejects full-body coverage": 'channel == "clothing_torso"' in GEN and "top >= 16 and bottom <= 52" in GEN,
    "hair selector excludes beards": 'semantic_channel(rel) == "scalp_hair"' in GEN,
    "long shirt restricted to torso channel": 'choose(files, "clothing_torso"' in GEN,
    "all-animation catalog": "lpc_character_animation_catalog_v0_1.json" in GEN and "build_animation_catalog" in GEN,
    "validator wired into build": "Validate-LpcCharacterSemanticChannelsV149J25.py" in BUILD,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    print("Pass 149J25 FAILED")
    for name in failed:
        print(f"- {name}")
    raise SystemExit(1)
print("Pass 149J25 strict LPC character semantic channels and animation catalog validated")
