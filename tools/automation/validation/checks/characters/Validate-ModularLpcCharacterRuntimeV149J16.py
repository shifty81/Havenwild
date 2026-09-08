from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
manifest_path = ROOT / "assets/generated/lpc/characters/havenwild_player_walk_64.json"
if not manifest_path.is_file():
    raise SystemExit(f"J17/Z7: missing generated character manifest: {manifest_path}")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

if manifest.get("schema") != "havenwild.universal_lpc.runtime_character_cache.v167z7":
    raise SystemExit("J17/Z7: runtime character cache is not generated from the Universal LPC authority")
if manifest.get("sourceAuthority") != "assets/source/licensed/universal_lpc_generator":
    raise SystemExit("J17/Z7: runtime character cache uses the wrong source authority")
if manifest.get("cellSize") != [64, 96]:
    raise SystemExit("J17/Z7: runtime character cache must use 64x96 cells")
if manifest.get("sourcePixelsPreservedAtOneToOne") is not True:
    raise SystemExit("J17/Z7: runtime character cache must preserve source pixels one-to-one")

required = {
    "body_male", "body_female", "eyes", "eyebrows_01_thin", "eyebrows_02_thick",
    "feet_boots", "feet_shoes", "feet_sandals",
    "legs_pants", "legs_skirt", "legs_shorts", "legs_long_skirt",
    "torso_tshirt", "torso_long_shirt", "torso_tunic", "torso_vest", "torso_apron",
    "hair_medium_01_page", "hair_medium_02_curly", "hair_medium_10_twists_fade",
    "hair_short_01_buzzcut", "hair_short_02_parted", "hair_short_08_flat_top_fade",
    "headwear_hat", "headwear_hood", "facial_hair_06_trimmed_beard",
    "facial_hair_07_medium_beard", "facial_hair_beard",
}
components = manifest.get("componentLayers", {})
missing = sorted(required - set(components))
if missing:
    raise SystemExit(f"J17/Z7: missing modular Universal LPC components: {missing}")
for component in sorted(required):
    path = ROOT / components[component]
    if not path.is_file():
        raise SystemExit(f"J17/Z7: missing generated component file for {component}: {path}")

provenance = manifest.get("componentSourceProvenance", {})
for component in sorted(required):
    sources = provenance.get(component)
    if not sources:
        raise SystemExit(f"J17/Z7: missing Universal LPC source provenance for {component}")
    for source_group in sources.values():
        for source in source_group:
            source_path = ROOT / "assets/source/licensed/universal_lpc_generator" / source
            if source.startswith(("/", "\\")) or ".." in Path(source).parts:
                raise SystemExit(f"J17/Z7: invalid source provenance for {component}: {source}")
            if not source_path.is_file():
                raise SystemExit(f"J17/Z7: missing Universal LPC provenance source for {component}: {source_path}")

creator = (ROOT / "crates/haven_game/src/client_frontend.rs").read_text(encoding="utf-8")
draw = (ROOT / "crates/haven_game/src/client_character_frontend_draw.rs").read_text(encoding="utf-8")
runtime = (ROOT / "crates/haven_game/src/character_runtime_compositor.rs").read_text(encoding="utf-8")
model = (ROOT / "crates/haven_game/src/character_creator_model.rs").read_text(encoding="utf-8")
for token in [
    "creator_option_rect", "EYE_PALETTES", "HeadwearKind", "FacialHairKind",
    "PreviewFacing", "preview_walking", "HairKind", "TorsoKind", "LegKind",
    "FootwearKind", "torso_apron", "legs_long_skirt", "feet_sandals",
]:
    if token not in creator + draw + model:
        raise SystemExit(f"J17/Z7: creator missing expanded option token {token}")
for token in [
    "generated_component_path", "face/facial_hair", "headwear_hat",
    "torso_tunic", 'value.starts_with("hair_")', "feet_sandals", "FilterMode::Nearest",
]:
    if token not in runtime:
        raise SystemExit(f"J17/Z7: runtime compositor missing expanded token {token}")

print(
    "Pass 149J17/Z7 modular Universal LPC character runtime validated: "
    f"{len(components)} generated component groups with source provenance, "
    "64x96 native grounding, compatibility filtering, direction and animation preview"
)
