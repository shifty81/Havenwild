#!/usr/bin/env python3
"""Build Havenwild runtime character caches from the complete Universal LPC repository.

Every output pixel is copied from a source sheet in the locked Universal LPC
Spritesheet Character Generator repository. The generated 64x96 sheets are
runtime caches only; source definitions and source paths remain authoritative.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Iterable

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "automation"))
from common.atomic_io import atomic_save_image, atomic_write_json
SOURCE = ROOT / "assets/source/licensed/universal_lpc_generator"
SPRITES = SOURCE / "spritesheets"
DEFINITIONS = SOURCE / "sheet_definitions"
OUTPUT_ROOT = ROOT / "assets/generated/lpc/characters"
LAYER_ROOT = OUTPUT_ROOT / "layers"
OUTPUT = OUTPUT_ROOT / "havenwild_player_walk_64.png"
MANIFEST = OUTPUT_ROOT / "havenwild_player_walk_64.json"
REVISION_PATH = OUTPUT_ROOT / ".generator_revision"
REVISION = "167Z109V1-authored-action-alias-and-directional-coverage-v1"
FRAME = 64
RUNTIME_H = 96
ROWS = 4
RUNTIME_COLUMNS = 9
RUNTIME_SIZE = (FRAME * RUNTIME_COLUMNS, RUNTIME_H * ROWS)

# Runtime component id -> Universal LPC sheet definition path.
HAIR = {
    "hair_medium_01_page": "hair/short/hair_page.json",
    "hair_medium_02_curly": "hair/curly/hair_curly_long.json",
    "hair_medium_03_idol": "hair/short/hair_idol.json",
    "hair_medium_04_bangs_bun": "hair/braids/hair_bangs_bun.json",
    "hair_medium_05_cornrows": "hair/afro/hair_cornrows.json",
    "hair_medium_06_dreadlocks": "hair/afro/hair_dreadlocks_long.json",
    "hair_medium_07_bob_side_part": "hair/bob/hair_bob_side_part.json",
    "hair_medium_08_bob_bangs": "hair/bob/hair_bob.json",
    "hair_medium_09_twists": "hair/afro/hair_twists_straight.json",
    "hair_medium_10_twists_fade": "hair/afro/hair_twists_fade.json",
    "hair_short_01_buzzcut": "hair/bald/hair_buzzcut.json",
    "hair_short_02_parted": "hair/short/hair_parted.json",
    "hair_short_03_curly": "hair/curly/hair_curly_short.json",
    "hair_short_04_cowlick": "hair/short/hair_cowlick.json",
    "hair_short_05_natural": "hair/afro/hair_natural.json",
    "hair_short_06_balding": "hair/bald/hair_balding.json",
    "hair_short_07_flat_top": "hair/afro/hair_flat_top_straight.json",
    "hair_short_08_flat_top_fade": "hair/afro/hair_flat_top_fade.json",
    "hair_parted": "hair/short/hair_parted.json",
    "hair_bob": "hair/bob/hair_bob.json",
    "hair_ponytail": "hair/braids/hair_high_ponytail.json",
    "hair_long": "hair/long/hair_long.json",
    "hair_curly": "hair/curly/hair_curly_long.json",
    "hair_mohawk": "hair/bald/hair_shorthawk.json",
    "hair_braid": "hair/braids/hair_braid.json",
    "hair_spiky": "hair/spiky/hair_spiked.json",
}

TORSO = {
    "torso_tshirt": "torso/shirts/shortsleeve/torso_clothes_tshirt.json",
    "torso_vneck_tshirt": "torso/shirts/shortsleeve/torso_clothes_tshirt_vneck.json",
    "torso_scoop_tshirt": "torso/shirts/shortsleeve/torso_clothes_tshirt_scoop.json",
    "torso_buttoned_tshirt": "torso/shirts/shortsleeve/torso_clothes_tshirt_buttoned.json",
    "torso_long_shirt": "torso/shirts/longsleeve/torso_clothes_longsleeve2.json",
    "torso_vneck_long_shirt": "torso/shirts/longsleeve/torso_clothes_longsleeve2_vneck.json",
    "torso_scoop_long_shirt": "torso/shirts/longsleeve/torso_clothes_longsleeve2_scoop.json",
    "torso_buttoned_long_shirt": "torso/shirts/longsleeve/torso_clothes_longsleeve2_buttoned.json",
    "torso_polo": "torso/shirts/shortsleeve/torso_clothes_shortsleeve_polo.json",
    "torso_tunic": "torso/shirts/torso_clothes_tunic.json",
    "torso_vest": "torso/vest/torso_clothes_vest.json",
    "torso_apron": "torso/aprons/torso_aprons_apron.json",
}

LEGS = {
    "legs_pants": "legs/pants/legs_pants.json",
    "legs_hose": "legs/leggings/legs_hose.json",
    "legs_leggings": "legs/leggings/legs_leggings.json",
    "legs_cuffed_pants": "legs/pants/legs_cuffed.json",
    "legs_overalls": "torso/aprons/torso_aprons_overalls.json",
    "legs_shorts": "legs/shorts/legs_shorts.json",
    "legs_short_shorts": "legs/shorts/legs_shorts_short.json",
    "legs_skirt": "legs/skirts/legs_skirts_plain.json",
    "legs_long_skirt": "legs/skirts/legs_skirt_straight.json",
}

FEET = {
    "feet_boots": "feet/boots/feet_boots_basic.json",
    "feet_shoes": "feet/shoes/feet_shoes_basic.json",
    "feet_ankle_socks": "feet/socks/feet_socks_ankle.json",
    "feet_high_socks": "feet/socks/feet_socks_high.json",
    "feet_sandals": "feet/feet_sandals.json",
}

FACE = {
    "eyebrows_01_thin": "head/eyebrows/eyebrows_thin.json",
    "eyebrows_02_thick": "head/eyebrows/eyebrows_thick.json",
    "facial_hair_01_walrus_mustache": "hair/mustaches/beards_walrus.json",
    "facial_hair_02_chevron_mustache": "hair/mustaches/beards_chevron.json",
    "facial_hair_03_handlebar_mustache": "hair/mustaches/beards_handlebar.json",
    "facial_hair_04_lampshade_mustache": "hair/mustaches/beards_lampshade.json",
    "facial_hair_05_horseshoe_mustache": "hair/mustaches/beards_horseshoe.json",
    "facial_hair_06_trimmed_beard": "hair/beards/beards_trimmed.json",
    "facial_hair_07_medium_beard": "hair/beards/beards_medium.json",
    "facial_hair_beard": "hair/beards/beards_trimmed.json",
}

HEADWEAR = {
    "headwear_hat": "headwear/hats/caps/hat_cap_leather.json",
    "headwear_hood": "headwear/coverings/hoods/hat_hood_cloth.json",
}

# Human heads are separate Universal LPC layers; body sheets intentionally
# contain only the neck-down anatomy. Compose the matching head into the
# body cache so every existing character profile receives a complete LPC body
# without requiring save migration or a Havenwild-authored fallback sprite.
HEAD = {
    "male": "head/heads/human/heads_human_male.json",
    "female": "head/heads/human/heads_human_female.json",
}

BODY_FALLBACKS = {
    "male": ("male",),
    "female": ("female",),
    "muscular": ("muscular",),
    "pregnant": ("pregnant",),
    "teen": ("teen",),
    "child": ("child",),
}
ANIMATION_FAMILIES = (
    "idle", "walk", "run", "jump", "climb", "sit", "emote", "combat",
    "1h_slash", "1h_backslash", "1h_halfslash", "watering", "thrust", "punch",
    "shoot", "hurt", "spellcast", "slash",
)
DIRECTION_INDEPENDENT_ACTIONS = {"climb", "hurt"}
BODY_HEAD_FALLBACK = {
    "male": "male",
    "muscular": "male",
    "teen": "male",
    "female": "female",
    "pregnant": "female",
    "child": None,
}


def load_definition(relative: str) -> dict:
    path = DEFINITIONS / relative
    if not path.is_file():
        raise FileNotFoundError(f"missing Universal LPC definition: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def choose_variant_file(directory: Path) -> Path | None:
    preferred = ("base.png", "default.png", "white.png", "brown.png", "black.png", "gray.png")
    for name in preferred:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    files = sorted(path for path in directory.glob("*.png") if path.is_file())
    return files[0] if files else None


ACTION_SOURCE_ALIASES = {
    "punch": ("thrust",),
    "combat": ("combat_idle",),
    "1h_slash": ("slash",),
    "1h_backslash": ("backslash",),
    "1h_halfslash": ("halfslash",),
    "watering": ("thrust",),
}


def resolve_action(prefix: str, animation: str) -> Path | None:
    root = SPRITES / prefix
    candidates = ACTION_SOURCE_ALIASES.get(animation, (animation,))
    for source_name in candidates:
        direct = root / f"{source_name}.png"
        if direct.is_file():
            return direct
        directory = root / source_name
        if directory.is_dir():
            selected = choose_variant_file(directory)
            if selected is not None:
                return selected
    if root.suffix.lower() == ".png" and root.is_file():
        return root
    return None


def layer_prefixes(definition: dict, body: str) -> list[tuple[int, str]]:
    result = []
    for key, layer in definition.items():
        if not key.startswith("layer_") or not isinstance(layer, dict):
            continue
        prefix = None
        for body_key in BODY_FALLBACKS[body]:
            value = layer.get(body_key)
            if isinstance(value, str):
                prefix = value
                break
        if prefix:
            result.append((int(layer.get("zPos", 0)), prefix))
    return sorted(result)


def source_paths_for_definition(relative: str, body: str, animation: str) -> list[Path]:
    definition = load_definition(relative)
    prefixes = layer_prefixes(definition, body)
    if not prefixes:
        return []
    paths = [resolve_action(prefix, animation) for _z, prefix in prefixes]
    # A multi-layer item is compatible only when every authored layer supports
    # the selected body and animation. This prevents half-rendered clothing.
    return [path for path in paths if path is not None] if all(paths) else []


def direct_paths(prefixes: Iterable[str], animation: str) -> list[Path]:
    paths = [resolve_action(prefix, animation) for prefix in prefixes]
    return [path for path in paths if path is not None] if all(paths) else []


def compose(paths: list[Path]) -> Image.Image:
    if not paths:
        raise FileNotFoundError("no Universal LPC source sheets resolved")
    layers = [Image.open(path).convert("RGBA") for path in paths]
    size = layers[0].size
    if any(layer.size != size for layer in layers):
        raise ValueError(f"Universal LPC layer geometry mismatch: {[layer.size for layer in layers]}")
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    for layer in layers:
        output.alpha_composite(layer)
    return output


def source_geometry(source: Image.Image) -> tuple[int, int]:
    """Return LPC frame columns/rows for a four-direction runtime source.

    Universal LPC contains a small number of legitimate partial animation
    strips, previews, and experimental actions that do not provide all four
    direction rows. Those files remain catalogued source material, but they
    cannot be promoted into Havenwild's four-direction runtime cache without
    inventing missing artwork.
    """
    if source.width % FRAME != 0 or source.height % FRAME != 0:
        raise ValueError(
            f"unsupported Universal LPC source geometry: {source.size}; "
            f"dimensions must be multiples of {FRAME}"
        )
    columns = source.width // FRAME
    rows = source.height // FRAME
    if columns < 1 or rows < ROWS:
        raise ValueError(
            f"unsupported Universal LPC source geometry: {source.size}; "
            f"expected at least {ROWS} directional rows of {FRAME}x{FRAME} cells"
        )
    return columns, rows


def source_frame(source: Image.Image, row: int, column: int) -> Image.Image:
    columns, _rows = source_geometry(source)
    column = min(max(column, 0), columns - 1)
    return source.crop((column * FRAME, row * FRAME, (column + 1) * FRAME, (row + 1) * FRAME))


def place(output: Image.Image, frame: Image.Image, column: int, row: int) -> None:
    output.alpha_composite(frame, (column * FRAME, row * RUNTIME_H + (RUNTIME_H - FRAME)))


def build_walk_or_idle_sheet(walk: Image.Image, idle: Image.Image | None, idle_only: bool) -> Image.Image:
    output = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    walk_columns, _walk_rows = source_geometry(walk)
    if idle is not None:
        source_geometry(idle)
    for row in range(ROWS):
        idle_frame = source_frame(idle, row, 0) if idle is not None else source_frame(walk, row, 0)
        for column in range(RUNTIME_COLUMNS):
            frame = idle_frame if idle_only or column == 0 else source_frame(walk, row, min(column - 1, walk_columns - 1))
            place(output, frame, column, row)
    return output


def build_action_sheet(source: Image.Image, direction_independent: bool = False) -> Image.Image:
    if source.width % FRAME != 0 or source.height % FRAME != 0:
        raise ValueError(f"unsupported Universal LPC source geometry: {source.size}")
    columns = source.width // FRAME
    rows = source.height // FRAME
    if columns < 1 or (rows < ROWS and not (direction_independent and rows == 1)):
        raise ValueError(
            f"unsupported Universal LPC action geometry: {source.size}; "
            "expected four directional rows or one authored direction-independent row"
        )
    output = Image.new("RGBA", (columns * FRAME, ROWS * RUNTIME_H), (0, 0, 0, 0))
    for row in range(ROWS):
        source_row = 0 if rows == 1 else row
        for column in range(columns):
            frame = source.crop((
                column * FRAME, source_row * FRAME,
                (column + 1) * FRAME, (source_row + 1) * FRAME,
            ))
            place(output, frame, column, row)
    return output


def animation_paths_for_definition(definition: str, body: str) -> dict[str, list[Path]]:
    return {
        animation: paths
        for animation in ANIMATION_FAMILIES
        if (paths := source_paths_for_definition(definition, body, animation))
    }


def animation_paths_for_direct(prefixes: Iterable[str]) -> dict[str, list[Path]]:
    return {
        animation: paths
        for animation in ANIMATION_FAMILIES
        if (paths := direct_paths(prefixes, animation))
    }


def merge_animation_paths(*sources: dict[str, list[Path]]) -> dict[str, list[Path]]:
    merged: dict[str, list[Path]] = {}
    for animation in ANIMATION_FAMILIES:
        parts = [source.get(animation, []) for source in sources]
        if all(parts):
            merged[animation] = [path for part in parts for path in part]
        elif len(sources) == 1 and parts[0]:
            merged[animation] = parts[0]
    return merged


def source_list(paths: list[Path]) -> list[str]:
    return [path.relative_to(SOURCE).as_posix() for path in paths]


def build_component(
    group_id: str,
    animation_paths: dict[str, list[Path]],
) -> tuple[dict, dict, dict, list[str]]:
    """Build one compatible component without letting partial actions kill it.

    Walk is the only mandatory authored movement source. Idle can fall back to
    the first walk frame. Every other action is promoted only when all layers
    compose and expose four LPC direction rows. Unsupported partial strips are
    recorded and omitted; the runtime already falls back to walk/idle when a
    component-specific action texture is unavailable.
    """
    if "walk" not in animation_paths:
        raise FileNotFoundError("no compatible walk source")

    outputs: dict[str, str] = {}
    geometry: dict[str, dict] = {}
    provenance: dict[str, list[str]] = {}
    omissions: list[str] = []

    try:
        walk = compose(animation_paths["walk"])
        source_geometry(walk)
    except Exception as error:
        raise ValueError(f"walk source is not runtime-compatible: {error}") from error

    idle: Image.Image | None = None
    idle_paths = animation_paths.get("idle")
    if idle_paths:
        try:
            idle = compose(idle_paths)
            source_geometry(idle)
        except Exception as error:
            omissions.append(
                f"{group_id}.idle: {error}; using first walk frame; "
                f"sources={source_list(idle_paths)}"
            )
            idle = None

    walk_image = build_walk_or_idle_sheet(walk, idle, idle_only=False)
    walk_output = LAYER_ROOT / f"havenwild_player_{group_id}_walk_64.png"
    atomic_save_image(walk_image, walk_output, optimize=False, compress_level=9)
    outputs["walk"] = walk_output.relative_to(ROOT).as_posix()
    geometry["walk"] = {
        "columns": walk_image.width // FRAME,
        "rows": ROWS,
        "cellSize": [FRAME, RUNTIME_H],
    }
    provenance["walk"] = source_list(animation_paths["walk"])

    idle_image = build_walk_or_idle_sheet(walk, idle, idle_only=True)
    idle_output = LAYER_ROOT / f"havenwild_player_{group_id}_idle_64.png"
    atomic_save_image(idle_image, idle_output, optimize=False, compress_level=9)
    outputs["idle"] = idle_output.relative_to(ROOT).as_posix()
    geometry["idle"] = {
        "columns": RUNTIME_COLUMNS,
        "rows": ROWS,
        "cellSize": [FRAME, RUNTIME_H],
    }
    if idle is None:
        geometry["idle"]["fallbackFrom"] = "walk"
        provenance["idle"] = provenance["walk"]
    else:
        provenance["idle"] = source_list(idle_paths or [])

    for animation in ANIMATION_FAMILIES:
        if animation in {"walk", "idle"}:
            continue
        paths = animation_paths.get(animation)
        if not paths:
            continue
        try:
            source = compose(paths)
            image = build_action_sheet(source, animation in DIRECTION_INDEPENDENT_ACTIONS)
        except Exception as error:
            omissions.append(
                f"{group_id}.{animation}: {error}; action omitted; "
                f"sources={source_list(paths)}"
            )
            continue
        output = LAYER_ROOT / f"havenwild_player_{group_id}_{animation}_64.png"
        atomic_save_image(image, output, optimize=False, compress_level=9)
        outputs[animation] = output.relative_to(ROOT).as_posix()
        geometry[animation] = {
            "columns": image.width // FRAME,
            "rows": ROWS,
            "cellSize": [FRAME, RUNTIME_H],
        }
        provenance[animation] = source_list(paths)

    return outputs, geometry, provenance, omissions

def body_group(body: str) -> dict[str, list[Path]]:
    direct = animation_paths_for_direct([f"body/bodies/{body}"])
    head_kind = BODY_HEAD_FALLBACK[body]
    if head_kind is None:
        return direct
    head = animation_paths_for_definition(HEAD[head_kind], head_kind)
    return merge_animation_paths(direct, head)


def main() -> int:
    if not SOURCE.is_dir():
        raise SystemExit("complete Universal LPC repository is not mounted")
    LAYER_ROOT.mkdir(parents=True, exist_ok=True)

    groups: dict[str, dict[str, list[Path]]] = {}
    for body in BODY_FALLBACKS:
        groups[f"body_{body}"] = body_group(body)
    groups["eyes"] = animation_paths_for_direct(["eyes/human/adult/neutral"])

    for group_id, definition in HAIR.items():
        for body in BODY_FALLBACKS:
            groups[f"{group_id}_{body}"] = animation_paths_for_definition(definition, body)
        groups[group_id] = groups[f"{group_id}_male"]
    for stem, definition in TORSO.items():
        for body in BODY_FALLBACKS:
            groups[f"{stem}_{body}"] = animation_paths_for_definition(definition, body)
        groups[stem] = groups[f"{stem}_male"]
    for stem, definition in LEGS.items():
        for body in BODY_FALLBACKS:
            groups[f"{stem}_{body}"] = animation_paths_for_definition(definition, body)
        groups[stem] = groups[f"{stem}_male"]
    for stem, definition in FEET.items():
        for body in BODY_FALLBACKS:
            groups[f"{stem}_{body}"] = animation_paths_for_definition(definition, body)
        groups[stem] = groups[f"{stem}_male"]
    for group_id, definition in FACE.items():
        for body in BODY_FALLBACKS:
            groups[f"{group_id}_{body}"] = animation_paths_for_definition(definition, body)
        groups[group_id] = groups[f"{group_id}_male"]
    for group_id, definition in HEADWEAR.items():
        for body in BODY_FALLBACKS:
            groups[f"{group_id}_{body}"] = animation_paths_for_definition(definition, body)
        groups[group_id] = groups[f"{group_id}_male"]

    layer_outputs: dict[str, dict] = {}
    geometry: dict[str, dict] = {}
    provenance: dict[str, dict] = {}
    optional_failures: list[str] = []
    required_groups = {"body_male", "body_female", "body_pregnant", "body_teen", "body_child"}
    for group_id, paths in sorted(groups.items()):
        if "walk" not in paths:
            if group_id in required_groups:
                raise RuntimeError(f"required Universal LPC body cache has no compatible walk source: {group_id}")
            optional_failures.append(f"{group_id}: no compatible walk source")
            continue
        try:
            outputs, output_geometry, sources, action_omissions = build_component(group_id, paths)
        except Exception as error:
            if group_id in required_groups:
                raise RuntimeError(f"required Universal LPC body cache failed: {group_id}: {error}") from error
            optional_failures.append(f"{group_id}: {error}")
            continue
        layer_outputs[group_id] = outputs
        geometry[group_id] = output_geometry
        provenance[group_id] = sources
        optional_failures.extend(action_omissions)

    default_order = ["body_male", "eyes", "feet_boots_male", "legs_pants_male", "torso_tshirt_male", "hair_short_02_parted"]
    assembled = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    for group_id in default_order:
        if group_id in layer_outputs:
            assembled.alpha_composite(Image.open(ROOT / layer_outputs[group_id]["walk"]).convert("RGBA"))
    atomic_save_image(assembled, OUTPUT, optimize=False, compress_level=9)

    manifest = {
        "id": "havenwild_player_walk_64",
        "schema": "havenwild.universal_lpc.runtime_character_cache.v167z42",
        "generatorRevision": REVISION,
        "sourceAuthority": "assets/source/licensed/universal_lpc_generator",
        "sourceCommit": "0f898bb675a1abe16ce430e82e3bf9daed278690",
        "kind": "universal_lpc_modular_character_runtime_cache",
        "output": OUTPUT.relative_to(ROOT).as_posix(),
        "cellSize": [FRAME, RUNTIME_H],
        "sourceCellSize": [FRAME, FRAME],
        "directions": ["north", "west", "south", "east"],
        "sourcePixelsPreservedAtOneToOne": True,
        "generatedCacheOnly": True,
        "componentLayers": {key: value["walk"] for key, value in layer_outputs.items()},
        "componentAnimations": layer_outputs,
        "componentAnimationGeometry": geometry,
        "componentAnimationAvailability": {
            key: sorted(value) for key, value in layer_outputs.items()
        },
        "componentSourceProvenance": provenance,
        "partialActionGeometryPolicy": "omit unsupported partial strips without fabricating missing direction rows",
        "bodyFamilies": sorted(BODY_FALLBACKS),
        "animationFamilies": list(ANIMATION_FAMILIES),
        "optionalCompatibilityOmissions": optional_failures,
        "completeRepositoryIndex": "content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz",
        "equipmentCatalog": "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json",
        "compatibilityMatrix": "content/characters/lpc_character_compatibility_matrix_v0_1.json",
    }
    atomic_write_json(MANIFEST, manifest)
    REVISION_PATH.write_text(REVISION + "\n", encoding="utf-8")
    unique_sources = {path for item in provenance.values() for paths in item.values() for path in paths}
    print(f"Wrote {len(layer_outputs)} compatible component groups across {len(ANIMATION_FAMILIES)} action families from {len(unique_sources)} source sheets")
    if optional_failures:
        print(f"Omitted {len(optional_failures)} incompatible optional component/body/action combinations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
