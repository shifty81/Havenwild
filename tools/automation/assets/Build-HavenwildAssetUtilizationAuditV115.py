#!/usr/bin/env python3
"""Build a planning-focused asset utilization audit for Havenwild.

This is intentionally a metadata audit, not a raw-pixel import step. It lists
the asset sources currently visible to the project, classifies their likely
use, and keeps license/production status explicit so the world editor can be
rebuilt around LPC without silently pulling in old or unaudited art.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "docs/assets/HAVENWILD_ASSET_UTILIZATION_AUDIT_PASS100.md"
IMAGE_EXTENSIONS = {".png", ".gif", ".webp", ".bmp", ".jpg", ".jpeg"}


@dataclass
class PackSummary:
    source: str
    pack_id: str
    display_name: str
    license_status: str
    files: int
    images: int
    category_counts: dict[str, int]
    utilization: str
    priority: str
    notes: str


def utilization_for_pack(pack_id: str, license_status: str, categories: dict[str, int]) -> tuple[str, str, str]:
    if "unknown" in license_status:
        return (
            "reference/hold",
            "blocked",
            "Do not promote until source and license are resolved.",
        )
    if pack_id == "elizawy_lpc_main":
        return (
            "canonical LPC source",
            "highest",
            "Primary source for terrain, interiors, structures, objects, characters, and editor palette rebuilds.",
        )
    if pack_id in {"lpc_atlas_base_terrain", "lpc_atlas_build_objects"}:
        return (
            "secondary LPC atlas/reference",
            "high",
            "Useful for coverage comparison and missing-object planning; import only through explicit attribution review.",
        )
    if "animal" in pack_id:
        return (
            "animal animation source",
            "medium",
            "Good candidate for the deferred original animal animation rebuild.",
        )
    if "plant" in pack_id:
        return (
            "foliage/object source",
            "medium",
            "Candidate for forage, crops, garden props, and object stamp extraction.",
        )
    if categories.get("foliage.tree", 0) or categories.get("structure.building", 0):
        return (
            "reference/object extraction candidate",
            "low",
            "Style and license are acceptable, but it should not displace LPC as the base set.",
        )
    return (
        "cataloged reference",
        "low",
        "Keep visible for planning; promote only with a specific gap it solves.",
    )


def read_json_bytes(data: bytes, label: str) -> dict:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive report detail
        return {"_error": f"{label}: {exc}"}


def summarize_zip(path: Path) -> tuple[list[PackSummary], str | None]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            catalog_names = []
            for name in names:
                parts = name.split("/")
                if (
                    "packs" in parts
                    and "/catalog/" in name
                    and name.lower().endswith(".json")
                ):
                    catalog_names.append(name)
            summaries: list[PackSummary] = []
            if not catalog_names:
                image_count = sum(1 for name in names if Path(name).suffix.lower() in IMAGE_EXTENSIONS)
                return [
                    PackSummary(
                        source=path.name,
                        pack_id=path.stem,
                        display_name=path.name,
                        license_status="uncataloged",
                        files=len(names),
                        images=image_count,
                        category_counts={},
                        utilization="uncataloged archive",
                        priority="inspect",
                        notes="Archive has no Havenwild pack catalog; run asset-pack-prepare before promotion.",
                    )
                ], None
            for catalog_name in catalog_names:
                payload = read_json_bytes(archive.read(catalog_name), catalog_name)
                if "_error" in payload:
                    summaries.append(
                        PackSummary(
                            source=path.name,
                            pack_id=catalog_name,
                            display_name=catalog_name,
                            license_status="unreadable_catalog",
                            files=0,
                            images=0,
                            category_counts={},
                            utilization="blocked",
                            priority="blocked",
                            notes=payload["_error"],
                        )
                    )
                    continue
                pack = payload.get("pack", {})
                summary = payload.get("summary", {})
                categories = dict(summary.get("categoryCounts", {}))
                utilization, priority, notes = utilization_for_pack(
                    pack.get("id", Path(catalog_name).stem),
                    pack.get("licenseStatus", "unknown"),
                    categories,
                )
                summaries.append(
                    PackSummary(
                        source=path.name,
                        pack_id=pack.get("id", Path(catalog_name).stem),
                        display_name=pack.get("displayName", Path(catalog_name).stem),
                        license_status=pack.get("licenseStatus", "unknown"),
                        files=int(summary.get("files", 0)),
                        images=int(summary.get("images", 0)),
                        category_counts=categories,
                        utilization=utilization,
                        priority=priority,
                        notes=notes,
                    )
                )
            return summaries, None
    except Exception as exc:
        return [], f"{path.name}: unreadable archive ({exc})"


def scan_tree(root: Path) -> dict:
    if not root.exists():
        return {"exists": False, "files": 0, "images": 0, "extensions": {}, "notable": []}
    files = [path for path in root.rglob("*") if path.is_file()]
    extensions = Counter(path.suffix.lower() or "[none]" for path in files)
    notable_needles = (
        "terrain",
        "autotile",
        "lpc",
        "asset_catalog",
        "environment",
        "object",
        "stamp",
        "player",
        "animal",
    )
    notable = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in files
        if any(needle in str(path).lower() for needle in notable_needles)
    ][:40]
    return {
        "exists": True,
        "files": len(files),
        "images": sum(1 for path in files if path.suffix.lower() in IMAGE_EXTENSIONS),
        "extensions": dict(extensions.most_common(12)),
        "notable": notable,
    }


def find_default_zips() -> list[Path]:
    candidates: list[Path] = []
    for base in (ROOT, ROOT.parent, ROOT / "project_sources", ROOT.parent / "project_sources"):
        if base.exists():
            candidates.extend(base.glob("*.zip"))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique


def markdown_table(rows: Iterable[Iterable[object]]) -> str:
    output = ["| Source | Pack | License/status | Files | Images | Use lane | Priority | Notes |"]
    output.append("| --- | --- | --- | ---: | ---: | --- | --- | --- |")
    for row in rows:
        output.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(output)


def build_report(zips: list[Path], output: Path) -> None:
    pack_summaries: list[PackSummary] = []
    archive_errors: list[str] = []
    for path in zips:
        summaries, error = summarize_zip(path)
        pack_summaries.extend(summaries)
        if error:
            archive_errors.append(error)

    tree_roots = [
        "assets",
        "content/assets",
        "content/assets/lpc",
        "content/assets/intake",
        "content/editor",
        "docs/assets",
    ]
    tree_summaries = {root: scan_tree(ROOT / root) for root in tree_roots}

    category_totals: Counter[str] = Counter()
    for summary in pack_summaries:
        category_totals.update(summary.category_counts)

    rows = [
        (
            summary.source,
            f"{summary.display_name} (`{summary.pack_id}`)",
            summary.license_status,
            summary.files,
            summary.images,
            summary.utilization,
            summary.priority,
            summary.notes,
        )
        for summary in sorted(pack_summaries, key=lambda item: (item.priority != "highest", item.pack_id))
    ]

    lines = [
        "# Havenwild Asset Utilization Audit — Pass 100",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Purpose: make the asset inventory actionable for rebuilding the world editor around LPC as the base tileset, while keeping old/generated/reference assets from quietly re-entering production.",
        "",
        "## Asset source inventory",
        "",
        markdown_table(rows) if rows else "_No external pack catalogs were found._",
        "",
        "## Local repository asset roots",
        "",
        "| Root | Exists | Files | Images | Top extensions | Notable planning files |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for root, summary in tree_summaries.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    root,
                    "yes" if summary["exists"] else "no",
                    str(summary["files"]),
                    str(summary["images"]),
                    ", ".join(f"{key}:{value}" for key, value in summary["extensions"].items()) or "-",
                    "<br>".join(summary["notable"][:8]) or "-",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Largest classified coverage areas",
            "",
            "| Class | Count | Planning use |",
            "| --- | ---: | --- |",
        ]
    )
    for category, count in category_totals.most_common(24):
        if category.startswith("terrain"):
            use = "terrain/floor/water migration and autotile coverage"
        elif category.startswith("environment") or category.startswith("structure"):
            use = "world-editor stamps, modular interiors/exteriors, cave/town props"
        elif category.startswith("foliage"):
            use = "forage, crop, tree, bush, and biome dressing"
        elif category.startswith("character") or category.startswith("animation"):
            use = "player/NPC/animal animation rebuild planning"
        elif category.startswith("ui"):
            use = "editor icon/reference only unless explicitly promoted"
        else:
            use = "manual review"
        lines.append(f"| `{category}` | {count} | {use} |")

    lines.extend(
        [
            "",
            "## Production plan",
            "",
            "1. Treat `elizawy_lpc_main` as the canonical LPC source. Terrain, caves, interiors, walls, floors, buildings, objects, and character animation should route through explicit LPC mapping contracts.",
            "2. Keep project-owned/generated Havenwild atlases as runtime outputs or temporary compatibility surfaces, not as the source of truth for new editor palette entries.",
            "3. Promote only seven terrain brushes first in the world editor: grass, dirt, sand, wet sand, pebble shore/path, shallow water, and deep water. Then add floor/wall/cave/interior groups once their LPC source cells are mapped.",
            "4. Use `lpc_atlas_base_terrain` and `lpc_atlas_build_objects` as comparison/reference packs for coverage gaps; do not bypass the pinned LPC dependency and mapping contracts.",
            "5. Keep Hyptosis, Artis, and unknown-license packs out of production runtime until their exact source/license and style fit are approved.",
            "6. Add object/stamp libraries by authored domain: interior, town/capital, cave, farm/forage, shoreline/dock, and building exterior. Each object should have an editor category, collision footprint, anchor, and runtime manifest entry.",
            "",
            "## Current blockers / risks",
            "",
        ]
    )
    if archive_errors:
        lines.extend(f"- {error}" for error in archive_errors)
    else:
        lines.append("- No unreadable archives were detected in the scanned set.")
    lines.extend(
        [
            "- Old generated placeholder atlases still exist as compatibility outputs; editor palette work should prefer LPC-backed semantic brushes and stamps.",
            "- Any pack marked `unknown_requires_review` is blocked from production promotion even if the pixels look useful.",
            "- Animal sheets are cataloged but intentionally deferred until the separate original animation rebuild.",
            "",
            "## Regeneration",
            "",
            "Run `./tools/build/Build.sh asset-utilization-audit [optional zip paths...]` after changing asset packs or adding a mounted asset library.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Havenwild asset utilization audit")
    parser.add_argument("zips", nargs="*", type=Path, help="Optional asset/source zip archives to include")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    zips = args.zips or find_default_zips()
    build_report(zips, args.output)
    print(f"Wrote {args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
