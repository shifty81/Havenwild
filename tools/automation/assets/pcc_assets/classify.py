from __future__ import annotations

from pathlib import Path
from typing import Any


REFERENCE_TOKENS = (
    "_ guides", "guides & palettes", "_ palette", "palette",
    "_ test scenes", "test scene", "demo", "example", "reference",
    "credits", "license", "licence", "readme",
)
TERRAIN_TOKENS = (
    "terrain", "cliff", "coast", "shore", "water", "grass", "dirt",
    "sand", "snow", "road", "path", "river", "pond", "ground",
    "mountain", "rock", "tile",
)
STRUCTURE_TOKENS = (
    "building", "structure", "house", "roof", "wall", "door", "window",
    "interior", "exterior", "fence", "bridge", "stairs", "ladder",
    "cave", "tavern", "shop", "barn", "shed",
)
CHARACTER_TOKENS = (
    "characters", "character", "body", "wardrobe", "hair", "beard",
    "head", "eyes", "clothes", "armor", "armour", "combat", "emotes",
)
UI_TOKENS = (
    "ui", "gui", "interface", "hud", "cursor", "button", "font",
)
ANIMATION_TOKENS = (
    "idle", "walk", "run", "jump", "climb", "slash", "thrust",
    "shoot", "spell", "hurt", "death", "sitting", "emotes",
)
VARIANT_CONTAINER_TOKENS = (
    "alternate", "variants", "variant", "colors", "colours",
    "skins", "palettes",
)
SEASONS = {"spring", "summer", "autumn", "fall", "winter"}
COLOR_WORDS = {
    "amber", "apple", "azure", "blue", "cerise", "charcoal", "coral",
    "cyan", "dove", "fern", "garnet", "green", "ice", "lavender",
    "lemon", "midnight", "mustard", "neptune", "ochre", "orange",
    "periwinkle", "plum", "purple", "red", "rose", "teal", "violet",
    "white", "yellow", "black", "brown", "gray", "grey",
}


def quick_png_dimensions(path: Path) -> tuple[int | None, int | None]:
    """Read PNG IHDR dimensions without decoding image pixels."""
    try:
        with path.open("rb") as fh:
            header = fh.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return None, None
        if header[12:16] != b"IHDR":
            return None, None
        return (
            int.from_bytes(header[16:20], "big"),
            int.from_bytes(header[20:24], "big"),
        )
    except OSError:
        return None, None


def classify_asset_path(
    relative_path: str,
    width: int | None = None,
    height: int | None = None,
    cell_width: int = 32,
    cell_height: int = 32,
) -> dict[str, Any]:
    lower = relative_path.replace("\\", "/").lower()
    name = Path(lower).name

    if any(token in lower for token in REFERENCE_TOKENS):
        domain = "reference"
    elif any(token in lower for token in CHARACTER_TOKENS):
        domain = "character"
    elif any(token in lower for token in STRUCTURE_TOKENS):
        domain = "structure"
    elif any(token in lower for token in TERRAIN_TOKENS):
        domain = "terrain"
    elif any(token in lower for token in UI_TOKENS):
        domain = "ui"
    elif any(token in name for token in ANIMATION_TOKENS):
        domain = "animation"
    else:
        domain = "prop"

    grid_compatible = bool(
        width and height
        and width % cell_width == 0
        and height % cell_height == 0
    )
    cells = (
        (width // cell_width) * (height // cell_height)
        if grid_compatible else None
    )

    if domain == "reference":
        route = "index_only"
    elif domain == "character":
        route = "character_family"
    elif domain == "ui":
        route = "index_only"
    elif not grid_compatible:
        route = "index_only"
    else:
        route = "sheet_deep"

    return {
        "domain": domain,
        "analyzerRoute": route,
        "gridCompatible": grid_compatible,
        "gridCellCount": cells,
    }


def variant_family_key(relative_path: str) -> str:
    """Normalize common variant/color/season paths into one family key."""
    parts = list(Path(relative_path.replace("\\", "/")).parts)
    lowered = [p.lower() for p in parts]

    # Generic "Alternate Colors/<variant>/Action.png" style.
    for i, part in enumerate(lowered[:-1]):
        if any(token in part for token in VARIANT_CONTAINER_TOKENS):
            if i + 1 < len(parts) - 1:
                parts[i + 1] = "{variant}"
            break

    # Seasonal source layouts often vary only by one folder or filename token.
    for i, part in enumerate(list(parts)):
        stem = Path(part).stem
        suffix = Path(part).suffix
        low = stem.lower()
        if low in SEASONS or low in COLOR_WORDS:
            parts[i] = "{variant}" + suffix
            continue
        for token in SEASONS:
            if token in low:
                parts[i] = stem.lower().replace(token, "{season}") + suffix
                break

    return "/".join(parts).lower()
