#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[3]
SLICE_CATALOG = Path("content/assets/lpc/lpc_slice_catalog_v0_1.json")
OUTPUT = Path("content/assets/lpc/structure_source_inventory_v1.json")
QUEUE_OUTPUT = Path("content/assets/lpc/structure_component_promotion_queue_v1.json")

FAMILY_ROLE = {
    "Bridges": "bridge",
    "Doors": "door",
    "Fences": "fence",
    "Floor": "floor",
    "Misc": "misc",
    "Pillars": "pillar",
    "Platforms": "platform",
    "Roofing": "roof",
    "Signs": "sign",
    "Stairs": "stairs",
    "Structures": "building_reference",
    "Wall Borders": "wall_border",
    "Walls": "wall",
    "Windows": "window",
}
ROLE_PRIORITY = {
    "door": 10, "stairs": 20, "fence": 30, "sign": 40,
    "floor": 50, "wall": 60, "wall_border": 70, "window": 80, "roof": 90,
    "bridge": 100, "platform": 110, "pillar": 120, "misc": 130,
    "building_reference": 900,
}

W45B_REVIEWED_SOURCES = {
    "assets/source/licensed/lpc_revised/Structure/Doors/32x48px Doors/12 Panel Door A.png",
    "assets/source/licensed/lpc_revised/Structure/Stairs/Short Steps A.png",
    "assets/source/licensed/lpc_revised/Structure/Fences/Plain Fence A.png",
    "assets/source/licensed/lpc_revised/Structure/Signs/Sign Backgrounds A.png",
    "assets/source/licensed/lpc_revised/Structure/Signs/Sign Icons A.png",
}
W45B_COMPONENT_CATALOG = Path("content/asset_packs/havenwild_objects/published_structure_components_v1.json")
W45C_REVIEWED_SOURCES = {
    "assets/source/licensed/lpc_revised/Structure/Floor/Wood Floor B.png",
    "assets/source/licensed/lpc_revised/Structure/Walls/Drywall.png",
    "assets/source/licensed/lpc_revised/Structure/Walls/CutawayOverlay.png",
    "assets/source/licensed/lpc_revised/Structure/Walls/Panels A.png",
    "assets/source/licensed/lpc_revised/Structure/Windows/Ornamental Windows B.png",
}
W45C_SURFACE_CATALOG = Path("content/asset_packs/havenwild_objects/published_structure_surfaces_v1.json")
W45C2_REVIEWED_SOURCES = {
    "assets/source/licensed/lpc_revised/Structure/Wall Borders/Formal Crown Molding.png",
}
W45C2_ROOF_TRIM_CATALOG = Path("content/asset_packs/havenwild_objects/published_structure_roof_trim_v1.json")
W45C3A_REVIEW_CONTRACT = Path("content/buildings/roof_exact_region_review_contract_v1.json")
W45D1_REVIEW_CONTRACT = Path("content/buildings/structure_support_exact_region_review_contract_v1.json")
W45D2_EXACT_MODULE_CATALOG = Path("content/asset_packs/havenwild_objects/published_structure_exact_modules_v1.json")
W45D2_REVIEWED_SOURCES = {
    "assets/source/licensed/lpc_revised/Structure/Roofing/Flat Shingle Roof A.png",
    "assets/source/licensed/lpc_revised/Structure/Roofing/Gable Shingle Roof A.png",
    "assets/source/licensed/lpc_revised/Structure/Bridges/Drawbridge A.png",
    "assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - No Rails.png",
    "assets/source/licensed/lpc_revised/Structure/Platforms/Dias with Steps A.png",
    "assets/source/licensed/lpc_revised/Structure/Pillars/Stone Pillar A.png",
    "assets/source/licensed/lpc_revised/Structure/Pillars/Floral Pillar A.png",
}

EXPECTED_COUNTS = {
    "bridge": 5,
    "door": 13,
    "fence": 3,
    "floor": 16,
    "misc": 5,
    "pillar": 2,
    "platform": 2,
    "roof": 7,
    "sign": 2,
    "stairs": 6,
    "building_reference": 3,
    "wall_border": 7,
    "wall": 20,
    "window": 7,
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    catalog = load(root / SLICE_CATALOG)
    # W45A remains the full pinned source inventory builder. Once the W45B
    # component catalog is repository-owned, rebuilding W45A must preserve the
    # exact source sheets that W45B reviewed instead of resetting progress.
    w45b_active = (root / W45B_COMPONENT_CATALOG).is_file()
    w45c_active = (root / W45C_SURFACE_CATALOG).is_file()
    w45c2_active = (root / W45C2_ROOF_TRIM_CATALOG).is_file()
    w45c3a_active = (root / W45C3A_REVIEW_CONTRACT).is_file()
    w45d1_active = (root / W45D1_REVIEW_CONTRACT).is_file()
    w45d2_active = (root / W45D2_EXACT_MODULE_CATALOG).is_file()
    reviewed_sources = set()
    if w45b_active:
        reviewed_sources.update(W45B_REVIEWED_SOURCES)
    if w45c_active:
        reviewed_sources.update(W45C_REVIEWED_SOURCES)
    if w45c2_active:
        reviewed_sources.update(W45C2_REVIEWED_SOURCES)
    if w45d2_active:
        reviewed_sources.update(W45D2_REVIEWED_SOURCES)
    entries = []
    counts = Counter()
    for sheet in catalog.get("sheets", []):
        source = str(sheet.get("source", ""))
        marker = "/Structure/"
        if marker not in source:
            continue
        tail = source.split(marker, 1)[1]
        source_family = tail.split("/", 1)[0]
        role = FAMILY_ROLE.get(source_family, "unclassified")
        counts[role] += 1
        entries.append({
            "id": sheet.get("id"),
            "sourcePath": source,
            "displayName": sheet.get("displayName"),
            "sourceFamily": source_family,
            "role": role,
            "imageSize": sheet.get("imageSize"),
            "sliceSize": sheet.get("sliceSize"),
            "grid": sheet.get("grid"),
            "sliceCount": sheet.get("sliceCount"),
            "nonEmptySliceCount": sheet.get("nonEmptySliceCount"),
            "likelyTileable": bool(sheet.get("likelyTileable")),
            "modularUse": sheet.get("modularUse"),
            "status": "COMPONENT_CANDIDATE" if source in reviewed_sources else "SOURCE_CANDIDATE",
            "certification": {
                "sourceCatalogued": True,
                "componentRectsReviewed": source in reviewed_sources,
                "runtimeCertified": False,
                "editorCertified": False,
            },
        })
    entries.sort(key=lambda e: (e["role"], e["sourcePath"].lower()))
    summary = {
        "totalSourceSheets": len(entries),
        "roleCounts": dict(sorted(counts.items())),
        "expectedRoleCounts": EXPECTED_COUNTS,
        "unclassified": counts.get("unclassified", 0),
        "reviewedComponentSourceSheets": sum(1 for e in entries if e["certification"]["componentRectsReviewed"]),
    }
    out = {
        "schema": "havenwild.structure_source_inventory.v1",
        "pass": "167Z109W45D2" if w45d2_active else ("167Z109W45D1" if w45d1_active else ("167Z109W45C3A" if w45c3a_active else ("167Z109W45C2" if w45c2_active else ("167Z109W45C" if w45c_active else ("167Z109W45B" if w45b_active else "167Z109W45A"))))),
        "sourceAuthority": "content/assets/lpc/lpc_slice_catalog_v0_1.json",
        "sourceRoot": catalog.get("sourceRoot", "assets/source/licensed/lpc_revised"),
        "policy": {
            "sourceSheetsAreNotPublishedComponents": True,
            "publishedComponentsUsePublishedWorldAssetRegistry": True,
            "generatedAtlasesAreCacheOnly": True,
            "requireExactSourceRectBeforePromotion": True,
            "badObjectKindSubstitutionsRemainForbidden": True,
            "buildingReferenceSheetsAreReferenceOnlyUntilDecomposed": True,
        },
        "summary": summary,
        "entries": entries,
    }
    output = root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    queue_entries = [
        {
            "sourceInventoryId": entry["id"],
            "sourcePath": entry["sourcePath"],
            "role": entry["role"],
            "priority": ROLE_PRIORITY.get(entry["role"], 800),
            "nextAction": (
                "inspect_structure_acceptance_scene"
                if entry["sourcePath"] in reviewed_sources
                else "review_exact_component_rects"
            ),
            "promotionTarget": (
                "reference_only_decompose_into_building_recipe"
                if entry["role"] == "building_reference"
                else (
                    "PublishedWorldAsset:structure_component_candidate"
                    if entry["sourcePath"] in reviewed_sources
                    else "PublishedWorldAsset:structure_component"
                )
            ),
        }
        for entry in entries
    ]
    queue_entries.sort(key=lambda e: (e["priority"], e["sourcePath"].lower()))
    queue = {
        "schema": "havenwild.structure_component_promotion_queue.v1",
        "pass": "167Z109W45D2" if w45d2_active else ("167Z109W45D1" if w45d1_active else ("167Z109W45C3A" if w45c3a_active else ("167Z109W45C2" if w45c2_active else ("167Z109W45C" if w45c_active else ("167Z109W45B" if w45b_active else "167Z109W45A"))))),
        "sourceInventory": OUTPUT.as_posix(),
        "currentBlockersFirst": ["door", "stairs", "fence", "sign"],
        "notes": [
            "The first four roles directly replace W43 fail-closed legacy structure/object substitutions.",
            "Do not promote a whole sheet. Review exact connected cells/stamps and publish components through PublishedWorldAssetRegistry.",
            "Building reference sheets remain decomposition references for W46 BuildingRecipe authority.",
            "When W45B/W45C/W45C2/W45D2 published catalogs are present, reviewed exact source sheets remain COMPONENT_CANDIDATE across deterministic W45A rebuilds. W45C3A and W45D1 evidence-only checkpoints do not mark additional sheets reviewed."
        ],
        "entries": queue_entries,
    }
    queue_output = root / QUEUE_OUTPUT
    queue_output.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    print(f"W45A structure source inventory: {len(entries)} sheet(s)")
    for role, count in sorted(counts.items()):
        print(f"- {role}: {count}")
    print(f"wrote {OUTPUT.as_posix()}")
    print(f"wrote {QUEUE_OUTPUT.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
