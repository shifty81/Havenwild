from pathlib import Path
import gzip
import json

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def require_text(path: str, token: str, label: str) -> None:
    target = ROOT / path
    if not target.is_file():
        errors.append(f"{path} missing {label}")
        return
    body = target.read_text(encoding="utf-8")
    if token not in body:
        errors.append(f"{path} missing {label}")


def load_json(path: str) -> dict:
    target = ROOT / path
    if not target.is_file():
        errors.append(f"{path} is missing")
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


summary = load_json("content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json")
equipment = load_json("content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json")
manifest = load_json("assets/generated/lpc/characters/havenwild_player_walk_64.json")

index_path = ROOT / "content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz"
if not index_path.is_file():
    errors.append("complete Universal LPC repository index is missing")
else:
    with gzip.open(index_path, "rt", encoding="utf-8") as stream:
        index = json.load(stream)
    if len(index.get("spritesheets", [])) != 88235:
        errors.append("complete Universal LPC index does not contain all 88,235 spritesheets")
    if len(index.get("sheetDefinitions", [])) != 768:
        errors.append("complete Universal LPC index does not contain all 768 sheet definitions")

if summary.get("spritesheetFiles") != 88235:
    errors.append("Universal LPC summary spritesheet count changed")
if summary.get("sheetDefinitionFiles") != 768:
    errors.append("Universal LPC summary sheet-definition count changed")
if equipment.get("equipmentCount") != 105:
    errors.append("Universal LPC equipment catalog does not expose all 105 definitions")
if manifest.get("sourceAuthority") != "assets/source/licensed/universal_lpc_generator":
    errors.append("runtime character cache is not sourced from the Universal LPC generator repository")
if manifest.get("generatedCacheOnly") is not True:
    errors.append("runtime character atlas must remain a disposable generated cache")

require_text(
    "tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py",
    "universal_lpc_equipment_action_catalog_v0_1.json",
    "complete character/equipment catalog generator",
)
require_text(
    "tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py",
    "sourcePixelsPreservedAtOneToOne",
    "source-pixel preservation contract",
)
require_text(
    "crates/haven_assets/src/universal_lpc_equipment_catalog.rs",
    "UniversalLpcEquipmentCatalog",
    "runtime equipment catalog loader",
)
require_text(
    "crates/haven_game/src/character_repository_catalog.rs",
    "creator_components",
    "runtime creator channel filter",
)
require_text(
    "crates/haven_game/src/character_repository_catalog.rs",
    "semantic_channel == semantic_channel",
    "strict semantic channel filtering",
)
require_text("crates/haven_game/src/main.rs", "mod character_repository_catalog;", "runtime catalog module registration")
require_text("crates/haven_game/Cargo.toml", "serde_json.workspace = true", "catalog JSON dependency")

if errors:
    print("Pass 149J28/Z7 FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print(
    "Pass 149J28/Z7 complete Universal LPC character, clothing, animation, tool, "
    "weapon, and shield production authority validated"
)
