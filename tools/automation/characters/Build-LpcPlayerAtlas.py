"""Build modular runtime player atlases from the pinned ElizaWy/LPC source tree."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "automation"))
from common.atomic_io import atomic_save_image, atomic_write_json
SOURCE_ROOT = ROOT / "assets/source/licensed/lpc_revised/Characters"
OUTPUT = ROOT / "assets/generated/lpc/characters/havenwild_player_walk_64.png"
MANIFEST = ROOT / "assets/generated/lpc/characters/havenwild_player_walk_64.json"
SHEET_CATALOG = ROOT / "content/assets/lpc/lpc_character_sheet_catalog_v0_1.json"
ANIMATION_CATALOG = ROOT / "content/assets/lpc/lpc_character_animation_catalog_v0_1.json"
LAYER_OUTPUT_ROOT = ROOT / "assets/generated/lpc/characters/layers"
CHARACTER_INVENTORY = ROOT / "content/assets/lpc/lpc_character_repository_inventory_v0_1.json"
PRODUCTION_CATALOG = ROOT / "content/assets/lpc/lpc_character_production_catalog_v0_1.json"
SOURCE_CELL = 64
RUNTIME_FRAME_WIDTH = 64
RUNTIME_FRAME_HEIGHT = 96
RUNTIME_TOP_PADDING = RUNTIME_FRAME_HEIGHT - SOURCE_CELL
RUNTIME_GROUND_ALPHA_Y = 92
CELL = SOURCE_CELL
GENERATOR_REVISION = "167Z4-native-64x96-idle-grounding-v2"
GENERATOR_REVISION_PATH = ROOT / "assets/generated/lpc/characters/.generator_revision"
SOURCE_COLUMNS = 8
RUNTIME_COLUMNS = 9
ROWS = 4
EXPECTED_SIZE = (SOURCE_COLUMNS * SOURCE_CELL, ROWS * SOURCE_CELL)
RUNTIME_SIZE = (RUNTIME_COLUMNS * RUNTIME_FRAME_WIDTH, ROWS * RUNTIME_FRAME_HEIGHT)

DEFAULTS = {
    "body_male": [
        "Body/Body 02 - Masculine, Thin/Tan/Walk.png",
        "Head/Head 02 - Masculine/Tan/Walk.png",
    ],
    "eyes": ["Head/Head Overlay - Eyes/Brown/Walk.png"],
    "feet_boots": ["Clothing/Masculine, Thin/Feet/Shoes 01 - Shoes/Brown/Walk.png"],
    "legs_pants": ["Clothing/Masculine, Thin/Legs/Pants 03 - Pants/Green/Walk.png"],
    "torso_tshirt": ["Clothing/Masculine, Thin/Torso/Shirt 04 - T-shirt/Blue/Walk.png"],
    "hair_short_02_parted": ["Hair/Short 02 - Parted/Brown/Walk.png"],
}


def walk_files() -> list[Path]:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"missing pinned LPC character root: {SOURCE_ROOT}")
    return [path for path in SOURCE_ROOT.rglob("Walk.png") if path.is_file()]


def relative(path: Path) -> str:
    return str(path.relative_to(SOURCE_ROOT)).replace("\\", "/")


def semantic_channel(relative_path: str) -> str:
    """Classify by strict LPC directory/filename semantics, never by broad head-region proximity."""
    text = relative_path.lower().replace("\\", "/")
    parts = text.split("/")
    if parts[0] == "hair":
        if "eyebrows" in text:
            return "eyebrows"
        if "facial hair" in text or any(token in text for token in ("beard", "moustache", "mustache")):
            return "facial_hair"
        return "scalp_hair"
    if parts[0] == "head":
        if any(token in text for token in ("beard", "moustache", "mustache", "facial")):
            return "facial_hair"
        if any(token in text for token in ("hood", "hat", "helmet", "cap", "crown", "headwear")):
            return "headwear"
        if "overlay" in text or any(token in text for token in ("eyes", "brows", "nose", "mouth", "scar", "makeup")):
            return "face_overlay"
        return "head_base"
    if parts[0] == "body":
        return "body"
    if parts[0] == "clothing":
        if "torso" in parts:
            return "clothing_torso"
        if "legs" in parts:
            return "clothing_legs"
        if "feet" in parts:
            return "clothing_feet"
        if any(token in text for token in ("hood", "hat", "helmet", "cap")):
            return "headwear"
        return "clothing_other"
    if parts[0] == "armor":
        return "armor"
    if parts[0] in ("weapons", "weapon"):
        return "weapon"
    return "character_related"



def layer_geometry_valid(path: Path, channel: str) -> bool:
    """Reject precomposited/full-body sheets from modular selectors using alpha coverage."""
    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        return False
    if image.size != EXPECTED_SIZE:
        return False
    # Sample every source frame. Coordinates are local to one 64x64 cell.
    occupied: list[tuple[int, int]] = []
    for row in range(ROWS):
        for column in range(SOURCE_COLUMNS):
            frame = image.crop((column * CELL, row * CELL, (column + 1) * CELL, (row + 1) * CELL))
            alpha = frame.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                occupied.append((bbox[1], bbox[3] - 1))
    if not occupied:
        return False
    top = min(value[0] for value in occupied)
    bottom = max(value[1] for value in occupied)
    if channel == "scalp_hair":
        return bottom <= 42
    if channel in ("facial_hair", "eyebrows", "face_overlay", "headwear", "head_base"):
        return bottom <= 46
    if channel == "clothing_torso":
        return top >= 16 and bottom <= 52
    if channel == "clothing_legs":
        return top >= 24 and bottom >= 42
    if channel == "clothing_feet":
        return top >= 38
    return True

def choose(files: list[Path], channel: str, include: tuple[str, ...] = (), prefer: tuple[str, ...] = (), exclude: tuple[str, ...] = ()) -> str | None:
    ranked: list[tuple[int, str]] = []
    for path in files:
        rel = relative(path)
        text = rel.lower()
        if semantic_channel(rel) != channel:
            continue
        if not layer_geometry_valid(path, channel):
            continue
        if any(token.lower() not in text for token in include):
            continue
        if any(token.lower() in text for token in exclude):
            continue
        score = sum(10 for token in prefer if token.lower() in text)
        score -= len(rel) // 50
        ranked.append((score, rel))
    return max(ranked, default=(0, None), key=lambda item: (item[0], item[1] or ""))[1]

def choose_body_component(
    files: list[Path],
    channel: str,
    body: str,
    style_tokens: tuple[str, ...],
    prefer: tuple[str, ...] = ("blue", "brown", "green"),
    exclude: tuple[str, ...] = (),
) -> str | None:
    exact = choose(files, channel, (body, *style_tokens), prefer, exclude)
    if exact:
        return exact
    # Some older LPC folders omit explicit body labels. Keep a visible fallback,
    # but record it through the source manifest rather than silently cloning pixels.
    return choose(files, channel, style_tokens, prefer, exclude)


def add_body_specific_creator_groups(
    groups: dict[str, list[str]], files: list[Path]
) -> None:
    torso_specs = {
        "torso_tshirt": ("shirt 04",),
        "torso_vneck_tshirt": ("shirt 05",),
        "torso_scoop_tshirt": ("shirt 06",),
        "torso_buttoned_tshirt": ("shirt 08",),
        "torso_long_shirt": ("shirt 01",),
        "torso_vneck_long_shirt": ("shirt 02",),
        "torso_scoop_long_shirt": ("shirt 03",),
        "torso_buttoned_long_shirt": ("shirt 07",),
        "torso_polo": ("shirt 09",),
        "torso_tunic": ("tunic",),
        "torso_vest": ("vest",),
        "torso_apron": ("apron",),
    }
    leg_specs = {
        "legs_pants": ("pants 03",),
        "legs_hose": ("pants 01",),
        "legs_leggings": ("pants 02",),
        "legs_cuffed_pants": ("pants 04",),
        "legs_overalls": ("pants 05",),
        "legs_shorts": ("shorts 01",),
        "legs_short_shorts": ("shorts 02",),
        "legs_skirt": ("skirt",),
        "legs_long_skirt": ("long", "skirt"),
    }
    feet_specs = {
        "feet_boots": ("shoes 02",),
        "feet_shoes": ("shoes 01",),
        "feet_ankle_socks": ("socks 01",),
        "feet_high_socks": ("socks 02",),
        "feet_sandals": ("sandal",),
    }
    body_tokens = {"male": "masculine", "female": "feminine"}
    for suffix, body_token in body_tokens.items():
        for stem, tokens in torso_specs.items():
            found = choose_body_component(
                files,
                "clothing_torso",
                body_token,
                tokens,
                exclude=("armor",),
            )
            groups[f"{stem}_{suffix}"] = [found] if found else list(groups.get(stem, []))
        for stem, tokens in leg_specs.items():
            found = choose_body_component(
                files,
                "clothing_legs",
                body_token,
                tokens,
                exclude=("armor",),
            )
            groups[f"{stem}_{suffix}"] = [found] if found else list(groups.get(stem, []))
        for stem, tokens in feet_specs.items():
            found = choose_body_component(
                files,
                "clothing_feet",
                body_token,
                tokens,
                exclude=("armor",),
            )
            groups[f"{stem}_{suffix}"] = [found] if found else list(groups.get(stem, []))


def discovered_groups() -> dict[str, list[str]]:
    files = walk_files()
    groups = dict(DEFAULTS)

    # Body variants must resolve to genuinely different source art. Prefer the
    # canonical LPC feminine-thin body/head pair and only fall back to discovered
    # feminine sheets; never alias the masculine composite silently.
    canonical_female = [
        "Body/Body 02 - Feminine, Thin/Tan/Walk.png",
        "Head/Head 02 - Feminine/Tan/Walk.png",
    ]
    female_paths = [rel for rel in canonical_female if (SOURCE_ROOT / rel).exists()]
    if len(female_paths) < 2:
        female_body = choose(files, "body", ("feminine",), ("thin", "tan"), ())
        female_head = choose(files, "head_base", ("feminine",), ("tan",), ())
        female_paths = [value for value in (female_body, female_head) if value]
    if not female_paths:
        raise FileNotFoundError("no feminine LPC body/head Walk sheets were found")
    groups["body_female"] = female_paths

    shoes = choose(files, "clothing_feet", (), ("shoe", "brown"), ("boot", "sandal"))
    groups["feet_shoes"] = [shoes] if shoes else []

    skirt = choose(files, "clothing_legs", ("feminine", "skirt"), ("brown", "green"), ())
    groups["legs_skirt"] = [skirt] if skirt else []

    long_shirt = choose(files, "clothing_torso", ("shirt",), ("long", "blue", "masculine"), ("body/", "head/"))
    groups["torso_long_shirt"] = [long_shirt] if long_shirt else []

    # Mirror the repository's exact Hair folder taxonomy. Missing entries remain
    # unavailable; they are never substituted with another hairstyle or beard.
    path = SOURCE_ROOT / "Hair/Medium 01 - Page/Brown/Walk.png"
    groups["hair_medium_01_page"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 02 - Curly/Brown/Walk.png"
    groups["hair_medium_02_curly"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 03 - Idol/Brown/Walk.png"
    groups["hair_medium_03_idol"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 04 - Bangs & Bun/Brown/Walk.png"
    groups["hair_medium_04_bangs_bun"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 05 - Cornrows/Brown/Walk.png"
    groups["hair_medium_05_cornrows"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 06 - Dreadlocks/Brown/Walk.png"
    groups["hair_medium_06_dreadlocks"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 07 - Bob, Side Part/Brown/Walk.png"
    groups["hair_medium_07_bob_side_part"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 08 - Bob, Bangs/Brown/Walk.png"
    groups["hair_medium_08_bob_bangs"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 09 - Twists/Brown/Walk.png"
    groups["hair_medium_09_twists"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Medium 10 - Twists, Fade/Brown/Walk.png"
    groups["hair_medium_10_twists_fade"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 01 - Buzzcut/Brown/Walk.png"
    groups["hair_short_01_buzzcut"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 02 - Parted/Brown/Walk.png"
    groups["hair_short_02_parted"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 03 - Curly/Brown/Walk.png"
    groups["hair_short_03_curly"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 04 - Cowlick/Brown/Walk.png"
    groups["hair_short_04_cowlick"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 05 - Natural/Brown/Walk.png"
    groups["hair_short_05_natural"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 06 - Balding/Brown/Walk.png"
    groups["hair_short_06_balding"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 07 - Flat Top/Brown/Walk.png"
    groups["hair_short_07_flat_top"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Short 08 - Flat Top, Fade/Brown/Walk.png"
    groups["hair_short_08_flat_top_fade"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "scalp_hair") else []
    path = SOURCE_ROOT / "Hair/Eyebrows 01 - Thin Eyebrows/Brown/Walk.png"
    groups["eyebrows_01_thin"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "eyebrows") else []
    path = SOURCE_ROOT / "Hair/Eyebrows 02 - Thick Eyebrows/Brown/Walk.png"
    groups["eyebrows_02_thick"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "eyebrows") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 01 - Walrus Mustache/Brown/Walk.png"
    groups["facial_hair_01_walrus_mustache"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 02 - Chevron Mustache/Brown/Walk.png"
    groups["facial_hair_02_chevron_mustache"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 03 - Handlebar Mustache/Brown/Walk.png"
    groups["facial_hair_03_handlebar_mustache"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 04 - Lampshade Mustache/Brown/Walk.png"
    groups["facial_hair_04_lampshade_mustache"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 05 - Horseshoe Mustache/Brown/Walk.png"
    groups["facial_hair_05_horseshoe_mustache"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 06 - Trimmed Beard/Brown/Walk.png"
    groups["facial_hair_06_trimmed_beard"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []
    path = SOURCE_ROOT / "Hair/Facial Hair 07 - Medium Beard/Brown/Walk.png"
    groups["facial_hair_07_medium_beard"] = [relative(path)] if path.exists() and layer_geometry_valid(path, "facial_hair") else []

    torso_specs = {
        "torso_tunic": (("clothing", "torso"), ("tunic", "green"), ()),
        "torso_vest": (("clothing", "torso"), ("vest", "brown"), ()),
        "torso_apron": (("clothing", "torso"), ("apron",), ()),
    }
    for group_id, (include, prefer, exclude) in torso_specs.items():
        found = choose(files, "clothing_torso", include, prefer, exclude)
        groups[group_id] = [found] if found else []

    leg_specs = {
        "legs_shorts": (("clothing", "legs"), ("short",), ("skirt",)),
        "legs_long_skirt": (("clothing", "legs"), ("long", "skirt"), ()),
    }
    for group_id, (include, prefer, exclude) in leg_specs.items():
        found = choose(files, "clothing_legs", include, prefer, exclude)
        groups[group_id] = [found] if found else []

    sandal = choose(files, "clothing_feet", (), ("sandal", "brown"), ("boot",))
    groups["feet_sandals"] = [sandal] if sandal else []

    hat = choose(files, "headwear", (), ("hat", "brown"), ("overlay", "hair"))
    hood = choose(files, "headwear", (), ("hood",), ("overlay", "hair"))
    groups["headwear_hat"] = [hat] if hat else []
    groups["headwear_hood"] = [hood] if hood else []

    add_body_specific_creator_groups(groups, files)
    return groups



def classify_sheet(relative_path: str) -> dict[str, object]:
    text = relative_path.lower()
    category = semantic_channel(relative_path)
    body = "feminine" if "feminine" in text else "masculine" if "masculine" in text else "universal"
    return {
        "source": relative_path,
        "animation": "walk",
        "frameSize": [CELL, CELL],
        "sourceGrid": [SOURCE_COLUMNS, ROWS],
        "category": category,
        "bodyCompatibility": body,
        "readyForLayering": True,
    }


def build_sheet_catalog(files: list[Path], selected_sources: set[str]) -> dict[str, object]:
    sheets = []
    for path in sorted(files):
        rel = str(path.relative_to(SOURCE_ROOT)).replace("\\", "/")
        record = classify_sheet(rel)
        record["selectedByStarterCreator"] = rel in selected_sources
        sheets.append(record)
    return {
        "schema": "havenwild.lpc.character-sheet-catalog.v1",
        "sourceRoot": "assets/source/licensed/lpc_revised/Characters",
        "animation": "Walk.png",
        "sheetCount": len(sheets),
        "sheets": sheets,
    }

def build_animation_catalog() -> dict[str, object]:
    records = []
    for path in sorted(SOURCE_ROOT.rglob("*.png")):
        if not path.is_file():
            continue
        rel = relative(path)
        animation = path.stem.lower().replace(" ", "_")
        records.append({
            "source": rel,
            "animation": animation,
            "semanticChannel": semantic_channel(rel),
            "bodyCompatibility": "feminine" if "feminine" in rel.lower() else "masculine" if "masculine" in rel.lower() else "universal",
            "productionState": "cataloged",
        })
    return {
        "schema": "havenwild.lpc.character-animation-catalog.v1",
        "sourceRoot": "assets/source/licensed/lpc_revised/Characters",
        "sheetCount": len(records),
        "animations": sorted({record["animation"] for record in records}),
        "sheets": records,
    }


def load_layer(relative_path: str) -> Image.Image:
    path = SOURCE_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing LPC player layer: {path}")
    layer = Image.open(path).convert("RGBA")
    if layer.size != EXPECTED_SIZE:
        raise ValueError(f"{relative_path} is {layer.size}; expected {EXPECTED_SIZE}")
    return layer


def compose_source_group(paths: list[str], tint_mask: bool = False) -> Image.Image:
    atlas = Image.new("RGBA", EXPECTED_SIZE, (0, 0, 0, 0))
    for relative_path in paths:
        atlas = Image.alpha_composite(atlas, load_layer(relative_path))
    if tint_mask:
        atlas = make_tint_mask(atlas)
    return atlas


def neutral_walk_column(source: Image.Image, row: int) -> int:
    """Choose one shared least-striding walk column from the body reference."""
    best = (10_000.0, 0)
    for column in range(SOURCE_COLUMNS):
        frame = source.crop((
            column * SOURCE_CELL,
            row * SOURCE_CELL,
            (column + 1) * SOURCE_CELL,
            (row + 1) * SOURCE_CELL,
        ))
        alpha = frame.getchannel("A")
        pixels = [
            (x, y)
            for y in range(SOURCE_CELL // 2, SOURCE_CELL)
            for x in range(SOURCE_CELL)
            if alpha.getpixel((x, y)) > 16
        ]
        if not pixels:
            continue
        xs = [x for x, _ in pixels]
        center = sum(xs) / len(xs)
        spread = max(xs) - min(xs)
        score = abs(center - (SOURCE_CELL - 1) / 2.0) * 3.0 + spread
        if score < best[0]:
            best = (score, column)
    return best[1]


def canonical_row_source_offsets(body_source: Image.Image) -> tuple[int, int, int, int]:
    """Place every layer using the body row baseline without scaling or clipping."""
    offsets: list[int] = []
    for row in range(ROWS):
        bottoms: list[int] = []
        for column in range(SOURCE_COLUMNS):
            frame = body_source.crop((
                column * SOURCE_CELL,
                row * SOURCE_CELL,
                (column + 1) * SOURCE_CELL,
                (row + 1) * SOURCE_CELL,
            ))
            bbox = frame.getchannel("A").getbbox()
            if bbox:
                bottoms.append(bbox[3] - 1)
        source_bottom = max(bottoms, default=SOURCE_CELL - 1)
        offsets.append(max(0, RUNTIME_GROUND_ALPHA_Y - source_bottom))
    return tuple(offsets)  # type: ignore[return-value]


def connected_alpha_components(image: Image.Image) -> list[list[tuple[int, int]]]:
    alpha = image.getchannel("A")
    occupied = {
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if alpha.getpixel((x, y)) > 0
    }
    components: list[list[tuple[int, int]]] = []
    while occupied:
        seed = occupied.pop()
        stack = [seed]
        component = [seed]
        while stack:
            x, y = stack.pop()
            for ny in range(max(0, y - 1), min(image.height, y + 2)):
                for nx in range(max(0, x - 1), min(image.width, x + 2)):
                    point = (nx, ny)
                    if point in occupied:
                        occupied.remove(point)
                        stack.append(point)
                        component.append(point)
        components.append(component)
    return components


def sanitize_frame(frame: Image.Image, remove_orphans: bool) -> Image.Image:
    """Remove only obvious one/two-pixel islands outside the primary sprite.

    This catches the transient pixel reported above the west-facing head while
    retaining authored face details. Tiny face-overlay channels opt out.
    """
    frame = frame.copy()
    pixels = frame.load()
    for y in range(frame.height):
        for x in range(frame.width):
            if pixels[x, y][3] == 0 and pixels[x, y][:3] != (0, 0, 0):
                pixels[x, y] = (0, 0, 0, 0)
    if not remove_orphans:
        return frame
    components = connected_alpha_components(frame)
    if len(components) < 2:
        return frame
    primary = max(components, key=len)
    primary_x = [x for x, _ in primary]
    primary_y = [y for _, y in primary]
    p_left, p_right = min(primary_x), max(primary_x)
    p_top, p_bottom = min(primary_y), max(primary_y)
    for component in components:
        if component is primary or len(component) > 2:
            continue
        xs = [x for x, _ in component]
        ys = [y for _, y in component]
        left, right = min(xs), max(xs)
        top, bottom = min(ys), max(ys)
        vertical_gap = max(p_top - bottom - 1, top - p_bottom - 1, 0)
        horizontal_gap = max(p_left - right - 1, left - p_right - 1, 0)
        if vertical_gap >= 3 or horizontal_gap >= 5:
            for x, y in component:
                pixels[x, y] = (0, 0, 0, 0)
    return frame


def place_source_frame(
    output: Image.Image,
    source_frame: Image.Image,
    runtime_column: int,
    row: int,
    source_y_offsets: tuple[int, int, int, int],
    remove_orphans: bool,
) -> None:
    runtime_frame = Image.new(
        "RGBA", (RUNTIME_FRAME_WIDTH, RUNTIME_FRAME_HEIGHT), (0, 0, 0, 0)
    )
    runtime_frame.alpha_composite(source_frame, (0, source_y_offsets[row]))
    runtime_frame = sanitize_frame(runtime_frame, remove_orphans)
    output.alpha_composite(
        runtime_frame,
        (runtime_column * RUNTIME_FRAME_WIDTH, row * RUNTIME_FRAME_HEIGHT),
    )


def expand_walk_to_runtime(
    source: Image.Image,
    neutral_columns: tuple[int, int, int, int],
    source_y_offsets: tuple[int, int, int, int],
    remove_orphans: bool,
) -> Image.Image:
    output = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    for row in range(ROWS):
        neutral_column = neutral_columns[row]
        idle = source.crop((
            neutral_column * SOURCE_CELL,
            row * SOURCE_CELL,
            (neutral_column + 1) * SOURCE_CELL,
            (row + 1) * SOURCE_CELL,
        ))
        place_source_frame(output, idle, 0, row, source_y_offsets, remove_orphans)
        for column in range(SOURCE_COLUMNS):
            frame = source.crop((
                column * SOURCE_CELL,
                row * SOURCE_CELL,
                (column + 1) * SOURCE_CELL,
                (row + 1) * SOURCE_CELL,
            ))
            place_source_frame(output, frame, column + 1, row, source_y_offsets, remove_orphans)
    return output


def expand_idle_to_runtime(
    source: Image.Image,
    source_y_offsets: tuple[int, int, int, int],
    remove_orphans: bool,
) -> Image.Image:
    if source.width % SOURCE_CELL != 0 or source.height != ROWS * SOURCE_CELL:
        raise ValueError(f"authored idle sheet has unsupported size {source.size}")
    source_columns = source.width // SOURCE_CELL
    selected_column = source_columns // 2
    output = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    for row in range(ROWS):
        frame = source.crop((
            selected_column * SOURCE_CELL,
            row * SOURCE_CELL,
            (selected_column + 1) * SOURCE_CELL,
            (row + 1) * SOURCE_CELL,
        ))
        for runtime_column in range(RUNTIME_COLUMNS):
            place_source_frame(
                output, frame, runtime_column, row, source_y_offsets, remove_orphans
            )
    return output


def idle_fallback_from_walk(
    source: Image.Image,
    neutral_columns: tuple[int, int, int, int],
    source_y_offsets: tuple[int, int, int, int],
    remove_orphans: bool,
) -> Image.Image:
    output = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    for row in range(ROWS):
        column = neutral_columns[row]
        frame = source.crop((
            column * SOURCE_CELL,
            row * SOURCE_CELL,
            (column + 1) * SOURCE_CELL,
            (row + 1) * SOURCE_CELL,
        ))
        for runtime_column in range(RUNTIME_COLUMNS):
            place_source_frame(
                output, frame, runtime_column, row, source_y_offsets, remove_orphans
            )
    return output

def animation_candidates(walk_relative_path: str, animation: str) -> list[Path]:
    directory = (SOURCE_ROOT / walk_relative_path).parent
    aliases = {
        "idle": ("Idle.png", "Stand.png", "Standing.png", "Idle 1.png", "Idle_1.png"),
        "walk": ("Walk.png",),
        "run": ("Run.png",),
        "slash": ("Slash.png", "Swing.png"),
        "thrust": ("Thrust.png",),
        "shoot": ("Shoot.png", "Bow.png"),
        "spellcast": ("Spellcast.png", "Spell Cast.png"),
        "hurt": ("Hurt.png", "Hit.png"),
        "sit": ("Sit.png", "Sitting.png"),
        "climb": ("Climb.png",),
        "carry": ("Carry.png",),
    }
    return [directory / name for name in aliases.get(animation, ()) if (directory / name).is_file()]


def build_animation_group(
    paths: list[str],
    animation: str,
    neutral_columns: tuple[int, int, int, int],
    source_y_offsets: tuple[int, int, int, int],
    tint_mask: bool = False,
    remove_orphans: bool = True,
) -> tuple[Image.Image, str]:
    selected: list[Path] = []
    for walk_path in paths:
        candidates = animation_candidates(walk_path, animation)
        if candidates:
            selected.append(candidates[0])
    if selected and len(selected) == len(paths):
        layers = [Image.open(path).convert("RGBA") for path in selected]
        size = layers[0].size
        if all(layer.size == size for layer in layers):
            atlas = Image.new("RGBA", size, (0, 0, 0, 0))
            for layer in layers:
                atlas = Image.alpha_composite(atlas, layer)
            if tint_mask:
                atlas = make_tint_mask(atlas)
            if animation == "idle":
                return expand_idle_to_runtime(atlas, source_y_offsets, remove_orphans), "authored"
    walk_source = compose_source_group(paths, tint_mask=tint_mask)
    return (
        idle_fallback_from_walk(
            walk_source, neutral_columns, source_y_offsets, remove_orphans
        ),
        "generated_neutral_from_walk",
    )

def build_repository_inventory() -> dict:
    records = []
    for path in sorted(SOURCE_ROOT.rglob("*.png")):
        rel = relative(path)
        parts = rel.split("/")
        records.append({
            "source": rel,
            "topLevel": parts[0] if parts else "",
            "componentFolder": "/".join(parts[:-2]) if len(parts) >= 3 else "/".join(parts[:-1]),
            "authoredVariant": parts[-2] if len(parts) >= 2 else "",
            "animation": path.stem,
            "semanticChannel": semantic_channel(rel),
        })
    channels = {}
    animations = {}
    for record in records:
        channels[record["semanticChannel"]] = channels.get(record["semanticChannel"], 0) + 1
        animations[record["animation"]] = animations.get(record["animation"], 0) + 1
    return {
        "schema": "havenwild.lpc.character.repository_inventory.v0_1",
        "sourceRoot": "assets/source/licensed/lpc_revised/Characters",
        "recordCount": len(records),
        "channelCounts": dict(sorted(channels.items())),
        "animationCounts": dict(sorted(animations.items())),
        "records": records,
    }



def build_production_catalog() -> dict:
    """Group the repository by authored component identity, color/variant, and animation.

    This catalog preserves the LPC folder taxonomy. Runtime/editor menus must consume
    these component records instead of inventing options or substituting unrelated
    sheets when an animation or color is unavailable.
    """
    components: dict[tuple[str, str, str], dict] = {}
    for path in sorted(SOURCE_ROOT.rglob("*.png")):
        if not path.is_file():
            continue
        rel = relative(path)
        parts = rel.split("/")
        if len(parts) < 2:
            continue
        channel = semantic_channel(rel)
        animation = path.stem
        authored_variant = parts[-2] if len(parts) >= 2 else "default"
        component_folder = "/".join(parts[:-2]) if len(parts) >= 3 else parts[0]
        top_level = parts[0]
        compatibility = "feminine" if "feminine" in rel.lower() else "masculine" if "masculine" in rel.lower() else "universal"
        key = (channel, component_folder, compatibility)
        record = components.setdefault(key, {
            "id": "",
            "displayName": component_folder.split("/")[-1] or component_folder,
            "semanticChannel": channel,
            "topLevel": top_level,
            "componentFolder": component_folder,
            "bodyCompatibility": compatibility,
            "authoredVariants": {},
            "animations": set(),
            "productionReady": False,
        })
        record["animations"].add(animation)
        variants = record["authoredVariants"]
        variants.setdefault(authored_variant, {})[animation] = rel

    records = []
    for index, ((channel, folder, compatibility), record) in enumerate(sorted(components.items()), start=1):
        slug = folder.lower().replace(" & ", "_and_")
        for token in ("/", " ", ",", "-", "(", ")", "'", "."):
            slug = slug.replace(token, "_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        record["id"] = f"lpc.{channel}.{slug.strip('_')}"
        record["animations"] = sorted(record["animations"])
        record["authoredVariants"] = {name: mapping for name, mapping in sorted(record["authoredVariants"].items())}
        # A component is production-ready for creator exposure only when it has a
        # Walk sheet in at least one authored variant and belongs to a modular slot.
        modular_channels = {
            "body", "head_base", "eyes", "eyebrows", "face_overlay",
            "scalp_hair", "facial_hair", "headwear", "clothing_torso",
            "clothing_legs", "clothing_feet", "armor", "weapon", "accessory",
        }
        record["productionReady"] = channel in modular_channels and any(
            "Walk" in animations or "walk" in {name.lower() for name in animations}
            for animations in record["authoredVariants"].values()
        )
        records.append(record)

    channel_counts: dict[str, int] = {}
    for record in records:
        channel_counts[record["semanticChannel"]] = channel_counts.get(record["semanticChannel"], 0) + 1
    return {
        "schema": "havenwild.lpc.character.production_catalog.v0_1",
        "sourceRoot": "assets/source/licensed/lpc_revised/Characters",
        "componentCount": len(records),
        "channelCounts": dict(sorted(channel_counts.items())),
        "components": records,
    }


def flattened_pixel_data(image: Image.Image):
    method = getattr(image, "get_flattened_data", None)
    return method() if method is not None else image.getdata()

def make_tint_mask(image: Image.Image) -> Image.Image:
    """Preserve authored alpha/shading while removing baked hue."""
    pixels = []
    for red, green, blue, alpha in flattened_pixel_data(image):
        if alpha == 0:
            pixels.append((0, 0, 0, 0))
            continue
        value = max(red, green, blue)
        pixels.append((value, value, value, alpha))
    masked = Image.new("RGBA", image.size)
    masked.putdata(pixels)
    return masked


def build_group(
    paths: list[str],
    neutral_columns: tuple[int, int, int, int],
    source_y_offsets: tuple[int, int, int, int],
    tint_mask: bool = False,
    remove_orphans: bool = True,
) -> Image.Image:
    source = compose_source_group(paths, tint_mask=tint_mask)
    return expand_walk_to_runtime(
        source, neutral_columns, source_y_offsets, remove_orphans
    )

def main() -> None:
    files = walk_files()
    groups = discovered_groups()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LAYER_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    body_reference = compose_source_group(groups["body_male"])
    neutral_columns = tuple(
        neutral_walk_column(body_reference, row) for row in range(ROWS)
    )
    source_y_offsets = canonical_row_source_offsets(body_reference)

    layer_outputs: dict[str, dict[str, str]] = {}
    animation_provenance: dict[str, dict[str, str]] = {}
    for group_id, paths in groups.items():
        if not paths:
            continue
        tint_mask = group_id == "eyes" or group_id.startswith("hair_") or group_id.startswith("eyebrows_") or group_id.startswith("facial_hair_")
        walk_path = LAYER_OUTPUT_ROOT / f"havenwild_player_{group_id}_walk_64.png"
        idle_path = LAYER_OUTPUT_ROOT / f"havenwild_player_{group_id}_idle_64.png"
        remove_orphans = not (
            group_id == "eyes"
            or group_id.startswith("eyebrows_")
            or group_id.startswith("facial_hair_")
        )
        atomic_save_image(
            build_group(
                paths,
                neutral_columns,
                source_y_offsets,
                tint_mask=tint_mask,
                remove_orphans=remove_orphans,
            ),
            walk_path,
            optimize=False,
            compress_level=9,
        )
        idle_image, idle_source = build_animation_group(
            paths,
            "idle",
            neutral_columns,
            source_y_offsets,
            tint_mask=tint_mask,
            remove_orphans=remove_orphans,
        )
        atomic_save_image(idle_image, idle_path, optimize=False, compress_level=9)
        layer_outputs[group_id] = {
            "walk": str(walk_path.relative_to(ROOT)).replace("\\", "/"),
            "idle": str(idle_path.relative_to(ROOT)).replace("\\", "/"),
        }
        animation_provenance[group_id] = {"walk": "authored", "idle": idle_source}

    assembled_order = [
        "body_male",
        "eyes",
        "eyebrows_01_thin",
        "feet_boots_male",
        "legs_pants_male",
        "torso_tshirt_male",
        "hair_short_02_parted",
    ]
    assembled = Image.new("RGBA", RUNTIME_SIZE, (0, 0, 0, 0))
    for group_id in assembled_order:
        assembled = Image.alpha_composite(assembled, build_group(groups[group_id], neutral_columns, source_y_offsets))
    atomic_save_image(assembled, OUTPUT, optimize=False, compress_level=9)

    selected_sources = {source for paths in groups.values() for source in paths}
    sheet_catalog = build_sheet_catalog(files, selected_sources)
    SHEET_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(SHEET_CATALOG, sheet_catalog)
    animation_catalog = build_animation_catalog()
    ANIMATION_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(ANIMATION_CATALOG, animation_catalog)
    repository_inventory = build_repository_inventory()
    CHARACTER_INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(CHARACTER_INVENTORY, repository_inventory)
    production_catalog = build_production_catalog()
    PRODUCTION_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(PRODUCTION_CATALOG, production_catalog)

    manifest = {
        "id": "havenwild_player_walk_64",
        "generatorRevision": GENERATOR_REVISION,
        "kind": "lpc_modular_character_walk_atlas",
        "sourceRoot": "assets/source/licensed/lpc_revised/Characters",
        "output": "assets/generated/lpc/characters/havenwild_player_walk_64.png",
        "cellSize": [RUNTIME_FRAME_WIDTH, RUNTIME_FRAME_HEIGHT],
        "sourceCellSize": [SOURCE_CELL, SOURCE_CELL],
        "runtimeGrid": [RUNTIME_COLUMNS, ROWS],
        "sourceGrid": [SOURCE_COLUMNS, ROWS],
        "sourceYOffsetByRow": list(source_y_offsets),
        "groundAlphaY": RUNTIME_GROUND_ALPHA_Y,
        "neutralWalkColumns": list(neutral_columns),
        "runtimeRows": ["north", "west", "south", "east"],
        "componentLayers": {key: value["walk"] for key, value in layer_outputs.items()},
        "componentAnimations": layer_outputs,
        "componentAnimationProvenance": animation_provenance,
        "componentSources": groups,
        "repositoryInventory": "content/assets/lpc/lpc_character_repository_inventory_v0_1.json",
        "repositoryInventoryRecordCount": repository_inventory["recordCount"],
        "productionCatalog": "content/assets/lpc/lpc_character_production_catalog_v0_1.json",
        "productionCatalogComponentCount": production_catalog["componentCount"],
        "fullCharacterSheetCatalog": "content/assets/lpc/lpc_character_sheet_catalog_v0_1.json",
        "fullCharacterSheetCount": sheet_catalog["sheetCount"],
        "fullCharacterAnimationCatalog": "content/assets/lpc/lpc_character_animation_catalog_v0_1.json",
        "fullCharacterAnimationSheetCount": animation_catalog["sheetCount"],
        "creatorVariants": {
            "body": ["body_male", "body_female"],
            "torso": [
                "torso_tshirt", "torso_vneck_tshirt", "torso_scoop_tshirt",
                "torso_buttoned_tshirt", "torso_long_shirt", "torso_vneck_long_shirt",
                "torso_scoop_long_shirt", "torso_buttoned_long_shirt", "torso_polo",
                "torso_tunic", "torso_vest", "torso_apron"
            ],
            "legs": [
                "legs_pants", "legs_hose", "legs_leggings", "legs_cuffed_pants",
                "legs_overalls", "legs_shorts", "legs_short_shorts", "legs_skirt",
                "legs_long_skirt"
            ],
            "feet": [
                "feet_boots", "feet_shoes", "feet_ankle_socks", "feet_high_socks",
                "feet_sandals"
            ],
            "bodySpecificSuffixes": ["male", "female"],
            "hair": ["hair_medium_01_page", "hair_medium_02_curly", "hair_medium_03_idol", "hair_medium_04_bangs_bun", "hair_medium_05_cornrows", "hair_medium_06_dreadlocks", "hair_medium_07_bob_side_part", "hair_medium_08_bob_bangs", "hair_medium_09_twists", "hair_medium_10_twists_fade", "hair_short_01_buzzcut", "hair_short_02_parted", "hair_short_03_curly", "hair_short_04_cowlick", "hair_short_05_natural", "hair_short_06_balding", "hair_short_07_flat_top", "hair_short_08_flat_top_fade"],
            "eyebrows": ["eyebrows_01_thin", "eyebrows_02_thick"],
            "headwear": ["none", "headwear_hat", "headwear_hood"],
            "facialHair": ["none", "facial_hair_01_walrus_mustache", "facial_hair_02_chevron_mustache", "facial_hair_03_handlebar_mustache", "facial_hair_04_lampshade_mustache", "facial_hair_05_horseshoe_mustache", "facial_hair_06_trimmed_beard", "facial_hair_07_medium_beard"]
        },
        "license": "OGA-BY 3.0",
        "attribution": ["Eliza Wyatt (DeathsDarling)", "LPC contributors"],
    }
    atomic_write_json(MANIFEST, manifest)
    GENERATOR_REVISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    GENERATOR_REVISION_PATH.write_text(GENERATOR_REVISION + "\n", encoding="utf-8")
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)}, {len(layer_outputs)} modular component families with walk+idle outputs, "
        f"cataloged {sheet_catalog['sheetCount']} Walk sheets, {animation_catalog['sheetCount']} total animation sheets, "
        f"{repository_inventory['recordCount']} repository PNG records, and {production_catalog['componentCount']} production component families"
    )


if __name__ == "__main__":
    main()
