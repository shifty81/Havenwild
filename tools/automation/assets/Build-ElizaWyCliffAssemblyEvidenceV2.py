#!/usr/bin/env python3
"""HW-CLIFF-SOURCE-02R2: multi-cell ElizaWy cliff assembly evidence.

This is an evidence tool only. It does not change runtime rendering, worldgen,
collision, traversal, or source art.

SOURCE-02 intentionally used conservative single-cell matching and found no
high-confidence c8/c15 evidence. R2 changes the evidence unit, not the
confidence policy: it searches source-native multi-cell rectangles containing
c8/c15 and requires matching pixels to be distributed across multiple source
cells. Ambiguous and partial candidates remain evidence only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PASS_ID = "HW-CLIFF-SOURCE-02R2"
SCHEMA = "havenwild.worldgen.elizawy_cliff_multicell_assembly_evidence.v2"
CELL = 32
COLS = 16
ROWS = 14

SOURCE_MOUNT = Path("assets/source/licensed/lpc_revised")
SUMMER_REL = SOURCE_MOUNT / "Terrain/cliff_summer.png"
DEMO_REL = SOURCE_MOUNT / "_ Test Scenes/DemoGame - 2 - Summer.png"
LANDSCAPE_REL = SOURCE_MOUNT / "_ Test Scenes/Test Landscape.png"

EXPECTED = {
    "cliff_summer.png": {
        "sha256": "94bd2ddb2c51677498453486092ef28e57e0c1880f4334359189229590298147",
        "dimensions": [512, 448],
    },
    "DemoGame - 2 - Summer.png": {
        "sha256": "0cd146b765a9c5acaef03ab140d969a76acad989cd3294268bbe8c2193a336c7",
        "dimensions": [1024, 1184],
    },
    "Test Landscape.png": {
        "sha256": "3eabde7ed7ce0b88ee14eddcc0ffad93a6259ef2dcd694319661d06398267d26",
        "dimensions": [1600, 400],
    },
}

# c8 is the unresolved complete transition/side-entry column in current
# Havenwild authority. c15 is the unresolved right-terminal neighborhood.
TARGETS = {
    "c8": {"column": 8, "priorityRows": list(range(0, 9))},
    "c15": {"column": 15, "priorityRows": list(range(0, 5))},
}

# Search only source-native rectangles. No rotate/mirror/stretch/crop synthesis.
SHAPES = (
    (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 1), (3, 1), (4, 1),
    (2, 2), (2, 3), (3, 2), (3, 3),
    (2, 4), (4, 2), (3, 4), (4, 3), (4, 4),
    (3, 5), (5, 3),
)

MIN_TOTAL_OPAQUE = 72
MIN_OCCUPIED_CELLS = 2
MIN_CELL_OPAQUE = 14
MIN_UNIQUE_COLORS = 10
SAMPLE_LIMIT = 72
ANCHOR_LIMIT = 8
SAMPLE_THRESHOLD = 0.58
PARTIAL_THRESHOLD = 0.68
STRONG_THRESHOLD = 0.84
CELL_SUPPORT_THRESHOLD = 0.60
MIN_SUPPORTED_CELLS = 2
MAX_CANDIDATE_ORIGINS = 16000
MAX_RESULTS_PER_STAMP_SCENE = 10
MAX_EXPORTED_PER_TARGET_SCENE = 24


def discover_repo(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    here = Path(__file__).resolve()
    if len(here.parents) >= 4:
        candidates.append(here.parents[3])
    candidates.extend([
        Path.cwd(),
        Path.home() / "Desktop" / "Havenwild-main",
        Path.home() / "Desktop" / "Havenwild",
    ])
    seen = set()
    for candidate in candidates:
        try:
            root = candidate.resolve()
        except OSError:
            continue
        if root in seen:
            continue
        seen.add(root)
        if (
            (root / "Cargo.toml").is_file()
            and (root / "crates/haven_game").is_dir()
            and (root / SUMMER_REL).is_file()
        ):
            return root
    raise FileNotFoundError("Could not locate Havenwild repository.")


def load_v1_module(repo: Path):
    path = (
        repo
        / "tools/automation/assets/"
        "Build-ElizaWyCliffDemoRelationshipEvidenceV1.py"
    )
    if not path.is_file():
        raise FileNotFoundError(
            "SOURCE-02 audit tool is missing. Apply HW-CLIFF-SOURCE-02/R1 first."
        )
    spec = importlib.util.spec_from_file_location("havenwild_cliff_source02_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load SOURCE-02 module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected_name: str, image: Any) -> dict[str, Any]:
    expected = EXPECTED[expected_name]
    actual_hash = digest(path)
    dims = [image.width, image.height]
    return {
        "path": path.as_posix(),
        "sha256": actual_hash,
        "dimensions": dims,
        "hashMatchesPinned": actual_hash == expected["sha256"],
        "dimensionsMatchPinned": dims == expected["dimensions"],
    }


def rgb_key(pixel: tuple[int, int, int, int]) -> int:
    r, g, b, _ = pixel
    return (r << 16) | (g << 8) | b


@dataclass(frozen=True)
class Stamp:
    target: str
    target_row: int
    left: int
    top: int
    width_cells: int
    height_cells: int
    target_offset_col: int
    target_offset_row: int

    @property
    def id(self) -> str:
        return (
            f"{self.target}_r{self.target_row}_"
            f"src_c{self.left}r{self.top}_"
            f"{self.width_cells}x{self.height_cells}"
        )


def enumerate_stamps() -> list[Stamp]:
    stamps: dict[tuple[Any, ...], Stamp] = {}
    for target_name, info in TARGETS.items():
        col = info["column"]
        for row in info["priorityRows"]:
            for w, h in SHAPES:
                for off_c in range(w):
                    for off_r in range(h):
                        left = col - off_c
                        top = row - off_r
                        if left < 0 or top < 0:
                            continue
                        if left + w > COLS or top + h > ROWS:
                            continue
                        stamp = Stamp(
                            target=target_name,
                            target_row=row,
                            left=left,
                            top=top,
                            width_cells=w,
                            height_cells=h,
                            target_offset_col=off_c,
                            target_offset_row=off_r,
                        )
                        key = (
                            stamp.target,
                            stamp.target_row,
                            stamp.left,
                            stamp.top,
                            stamp.width_cells,
                            stamp.height_cells,
                        )
                        stamps[key] = stamp
    return sorted(
        stamps.values(),
        key=lambda s: (
            s.target, s.target_row,
            s.width_cells * s.height_cells,
            s.top, s.left,
        ),
    )


def opaque_points(source: Any, stamp: Stamp) -> tuple[
    list[tuple[int, int, int, int, int]],
    dict[tuple[int, int], list[tuple[int, int, int]]],
]:
    points = []
    by_cell: dict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(list)
    x0 = stamp.left * CELL
    y0 = stamp.top * CELL
    for ly in range(stamp.height_cells * CELL):
        for lx in range(stamp.width_cells * CELL):
            r, g, b, a = source.pixel(x0 + lx, y0 + ly)
            if a < 250:
                continue
            key = (r << 16) | (g << 8) | b
            cell_x = lx // CELL
            cell_y = ly // CELL
            points.append((lx, ly, key, cell_x, cell_y))
            by_cell[(cell_x, cell_y)].append((lx, ly, key))
    return points, by_cell


def color_counts(image: Any) -> Counter[int]:
    counts: Counter[int] = Counter()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = image.pixel(x, y)
            if a > 0:
                counts[(r << 16) | (g << 8) | b] += 1
    return counts


def positions_for_colors(image: Any, colors: set[int]) -> dict[int, list[tuple[int, int]]]:
    out = {c: [] for c in colors}
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = image.pixel(x, y)
            if a == 0:
                continue
            key = (r << 16) | (g << 8) | b
            if key in out:
                out[key].append((x, y))
    return out


def spatially_distributed(
    points: list[tuple[int, int, int, int, int]],
    scene_counts: Counter[int],
    limit: int,
) -> list[tuple[int, int, int, int, int]]:
    ordered = sorted(
        points,
        key=lambda p: (
            scene_counts.get(p[2], 0),
            p[4], p[3], p[1], p[0],
        ),
    )
    chosen = []
    for p in ordered:
        if all(
            abs(p[0] - q[0]) + abs(p[1] - q[1]) >= 7
            for q in chosen
        ):
            chosen.append(p)
        if len(chosen) >= limit:
            break
    if len(chosen) < min(limit, len(ordered)):
        for p in ordered:
            if p not in chosen:
                chosen.append(p)
            if len(chosen) >= limit:
                break
    return chosen


def exact_score(
    scene: Any,
    origin_x: int,
    origin_y: int,
    points: Iterable[tuple[int, int, int, int, int] | tuple[int, int, int]],
) -> tuple[int, int]:
    hits = 0
    total = 0
    for p in points:
        lx, ly, key = p[0], p[1], p[2]
        sx = origin_x + lx
        sy = origin_y + ly
        total += 1
        if sx < 0 or sy < 0 or sx >= scene.width or sy >= scene.height:
            continue
        r, g, b, _ = scene.pixel(sx, sy)
        if ((r << 16) | (g << 8) | b) == key:
            hits += 1
    return hits, total


def match_stamp(source: Any, scene: Any, stamp: Stamp, cache: dict[str, Any]) -> dict[str, Any]:
    points, by_cell = opaque_points(source, stamp)
    occupied = {
        cell: pts
        for cell, pts in by_cell.items()
        if len(pts) >= MIN_CELL_OPAQUE
    }
    unique_colors = {p[2] for p in points}
    if (
        len(points) < MIN_TOTAL_OPAQUE
        or len(occupied) < MIN_OCCUPIED_CELLS
        or len(unique_colors) < MIN_UNIQUE_COLORS
    ):
        return {
            "stamp": stamp.id,
            "eligible": False,
            "reason": "insufficient_spatial_source_evidence",
            "opaquePixels": len(points),
            "occupiedCells": len(occupied),
            "uniqueColors": len(unique_colors),
            "matches": [],
        }

    counts: Counter[int] = cache["counts"]
    sample = spatially_distributed(points, counts, SAMPLE_LIMIT)
    anchor_candidates = spatially_distributed(points, counts, ANCHOR_LIMIT)
    if not anchor_candidates:
        return {
            "stamp": stamp.id,
            "eligible": False,
            "reason": "no_anchor_pixels",
            "opaquePixels": len(points),
            "occupiedCells": len(occupied),
            "uniqueColors": len(unique_colors),
            "matches": [],
        }

    positions = cache["positions"]
    # Pick the rarest anchor that actually occurs in the scene.
    anchor = None
    for p in anchor_candidates:
        if positions.get(p[2]):
            anchor = p
            break
    if anchor is None:
        return {
            "stamp": stamp.id,
            "eligible": True,
            "reason": "anchor_colors_not_present_in_scene",
            "opaquePixels": len(points),
            "occupiedCells": len(occupied),
            "uniqueColors": len(unique_colors),
            "matches": [],
        }

    ax, ay, acolor = anchor[0], anchor[1], anchor[2]
    origins = []
    seen = set()
    for px, py in positions.get(acolor, []):
        ox = px - ax
        oy = py - ay
        if (ox, oy) in seen:
            continue
        seen.add((ox, oy))
        if ox < 0 or oy < 0:
            continue
        if ox + stamp.width_cells * CELL > scene.width:
            continue
        if oy + stamp.height_cells * CELL > scene.height:
            continue
        origins.append((ox, oy))
        if len(origins) >= MAX_CANDIDATE_ORIGINS:
            break

    results = []
    for ox, oy in origins:
        sample_hits, sample_total = exact_score(scene, ox, oy, sample)
        sample_score = sample_hits / sample_total if sample_total else 0.0
        if sample_score < SAMPLE_THRESHOLD:
            continue

        hits, total = exact_score(scene, ox, oy, points)
        score = hits / total if total else 0.0
        if score < PARTIAL_THRESHOLD:
            continue

        cell_scores = {}
        supported = 0
        for (cx, cy), cell_points in occupied.items():
            ch, ct = exact_score(scene, ox, oy, cell_points)
            cs = ch / ct if ct else 0.0
            cell_scores[f"{cx},{cy}"] = round(cs, 6)
            if cs >= CELL_SUPPORT_THRESHOLD:
                supported += 1

        if supported < MIN_SUPPORTED_CELLS:
            continue

        class_name = "strong" if score >= STRONG_THRESHOLD else "partial"
        # Ranking rewards exact coverage, multiple independently supported
        # cells, and larger evidence payloads. It does not imply certification.
        rank = (
            score
            * (1.0 + math.log2(max(2, hits)))
            * (1.0 + 0.18 * supported)
        )
        results.append({
            "sceneX": ox,
            "sceneY": oy,
            "score": round(score, 6),
            "sampleScore": round(sample_score, 6),
            "matchedPixels": hits,
            "sourceOpaquePixels": total,
            "supportedCells": supported,
            "occupiedCells": len(occupied),
            "cellScores": cell_scores,
            "classification": class_name,
            "rank": round(rank, 6),
        })

    results.sort(
        key=lambda r: (
            -r["rank"],
            -r["score"],
            -r["supportedCells"],
            r["sceneY"],
            r["sceneX"],
        )
    )
    return {
        "stamp": stamp.id,
        "eligible": True,
        "reason": None,
        "opaquePixels": len(points),
        "occupiedCells": len(occupied),
        "uniqueColors": len(unique_colors),
        "sourceRectCells": [
            stamp.left, stamp.top, stamp.width_cells, stamp.height_cells
        ],
        "target": stamp.target,
        "targetRow": stamp.target_row,
        "targetOffsetCells": [
            stamp.target_offset_col, stamp.target_offset_row
        ],
        "matches": results[:MAX_RESULTS_PER_STAMP_SCENE],
    }


def make_scene_cache(scene: Any, all_anchor_colors: set[int]) -> dict[str, Any]:
    return {
        "counts": color_counts(scene),
        "positions": positions_for_colors(scene, all_anchor_colors),
    }


def candidate_anchor_colors(source: Any, stamps: list[Stamp]) -> set[int]:
    colors = set()
    for stamp in stamps:
        pts, _ = opaque_points(source, stamp)
        # All source colors are safe here; scene indexing is built only once.
        colors.update(p[2] for p in pts)
    return colors


def flatten_candidates(
    scene_name: str,
    stamp_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for result in stamp_results:
        if not result.get("matches"):
            continue
        for match in result["matches"]:
            row = {
                "scene": scene_name,
                "stamp": result["stamp"],
                "target": result["target"],
                "targetRow": result["targetRow"],
                "sourceRectCells": result["sourceRectCells"],
                "targetOffsetCells": result["targetOffsetCells"],
                **match,
            }
            rows.append(row)
    rows.sort(
        key=lambda r: (
            r["target"],
            -r["rank"],
            -r["score"],
            r["sceneY"],
            r["sceneX"],
            r["stamp"],
        )
    )
    return rows


def dedupe_visual_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the strongest candidate for near-identical scene placements.

    Large and small source rectangles can describe the same demonstrated
    neighborhood. We preserve the stronger multi-cell explanation for crop
    generation while all raw candidates remain in JSON.
    """
    kept = []
    for row in sorted(rows, key=lambda r: (-r["rank"], -r["score"])):
        x, y = row["sceneX"], row["sceneY"]
        w = row["sourceRectCells"][2] * CELL
        h = row["sourceRectCells"][3] * CELL
        overlaps = False
        for prior in kept:
            if prior["target"] != row["target"]:
                continue
            px, py = prior["sceneX"], prior["sceneY"]
            pw = prior["sourceRectCells"][2] * CELL
            ph = prior["sourceRectCells"][3] * CELL
            ix = max(0, min(x + w, px + pw) - max(x, px))
            iy = max(0, min(y + h, py + ph) - max(y, py))
            intersection = ix * iy
            smaller = min(w * h, pw * ph)
            if smaller and intersection / smaller >= 0.70:
                overlaps = True
                break
        if not overlaps:
            kept.append(row)
    return kept


def export_candidates(
    v1: Any,
    source: Any,
    scene: Any,
    scene_label: str,
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> list[dict[str, Any]]:
    written = []
    safe_scene = scene_label.replace(" ", "_").replace("/", "_")
    by_target: dict[str, int] = defaultdict(int)

    for row in dedupe_visual_candidates(rows):
        target = row["target"]
        if by_target[target] >= MAX_EXPORTED_PER_TARGET_SCENE:
            continue
        by_target[target] += 1

        left, top, wc, hc = row["sourceRectCells"]
        source_crop = v1.crop(
            source, left * CELL, top * CELL, wc * CELL, hc * CELL
        )
        scene_crop = v1.crop(
            scene, row["sceneX"], row["sceneY"], wc * CELL, hc * CELL
        )
        prefix = (
            f"{safe_scene}_{target}_{by_target[target]:02d}_"
            f"{row['classification']}_{row['score']:.3f}_"
            f"{row['stamp']}"
        )
        source_name = prefix + "_SOURCE.png"
        scene_name = prefix + "_SCENE.png"
        v1.encode_png(output_dir / source_name, source_crop)
        v1.encode_png(output_dir / scene_name, scene_crop)
        written.append({
            "target": target,
            "stamp": row["stamp"],
            "classification": row["classification"],
            "score": row["score"],
            "source": source_name,
            "scene": scene_name,
        })
    return written


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for target in TARGETS:
        target_rows = [r for r in rows if r["target"] == target]
        strong = [r for r in target_rows if r["classification"] == "strong"]
        partial = [r for r in target_rows if r["classification"] == "partial"]
        out[target] = {
            "candidateCount": len(target_rows),
            "strongCount": len(strong),
            "partialCount": len(partial),
            "best": strong[:8] if strong else partial[:8],
        }
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scene", "target", "targetRow", "stamp",
        "sourceLeft", "sourceTop", "sourceWidthCells", "sourceHeightCells",
        "sceneX", "sceneY", "classification", "score", "sampleScore",
        "matchedPixels", "sourceOpaquePixels", "supportedCells",
        "occupiedCells", "rank",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            left, top, wc, hc = r["sourceRectCells"]
            writer.writerow({
                "scene": r["scene"],
                "target": r["target"],
                "targetRow": r["targetRow"],
                "stamp": r["stamp"],
                "sourceLeft": left,
                "sourceTop": top,
                "sourceWidthCells": wc,
                "sourceHeightCells": hc,
                "sceneX": r["sceneX"],
                "sceneY": r["sceneY"],
                "classification": r["classification"],
                "score": r["score"],
                "sampleScore": r["sampleScore"],
                "matchedPixels": r["matchedPixels"],
                "sourceOpaquePixels": r["sourceOpaquePixels"],
                "supportedCells": r["supportedCells"],
                "occupiedCells": r["occupiedCells"],
                "rank": r["rank"],
            })


def markdown(authority: dict[str, Any]) -> str:
    lines = [
        "# HW-CLIFF-SOURCE-02R2 — Multi-Cell Assembly Evidence",
        "",
        "This is **evidence only**. No runtime/worldgen/collision/traversal change is authorized.",
        "",
        "## Why SOURCE-02R2 exists",
        "",
        "SOURCE-02 single-cell evidence was too weak: the official Summer demo resolved only one unique scene position and Test Landscape produced many repeated/ambiguous color hits. c8 and c15 had no high-confidence standalone-cell matches.",
        "",
        "R2 therefore changes the evidence unit from one 32×32 cell to source-native multi-cell rectangles containing c8/c15. It does not lower the source-authority standard.",
        "",
    ]
    for scene, data in authority["scenes"].items():
        lines += [f"## {scene}", ""]
        for target, summary in data["summary"].items():
            lines.append(
                f"- **{target}**: {summary['candidateCount']} candidates "
                f"({summary['strongCount']} strong, {summary['partialCount']} partial)"
            )
            for best in summary["best"][:4]:
                rect = best["sourceRectCells"]
                lines.append(
                    f"  - `{best['stamp']}` source={rect} scene=({best['sceneX']},"
                    f"{best['sceneY']}) score={best['score']} "
                    f"supportedCells={best['supportedCells']}"
                )
        lines.append("")
    lines += [
        "## Certification gate",
        "",
        "- `strong` means stronger visual evidence, **not runtime certification**.",
        "- No mirror, rotation, stretch, or foreign-family substitution is tested.",
        "- SOURCE-03 must review exact SOURCE/SCENE crop pairs before promoting an assembly.",
        "- If c8/c15 still produce no strong multi-cell evidence, the official demo does not prove those relationships sufficiently; use TSX/Tiled or other upstream source evidence instead of guessing.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--strict-pinned-hashes", action="store_true")
    args = parser.parse_args()

    try:
        repo = discover_repo(args.repo_root)
        v1 = load_v1_module(repo)
    except (FileNotFoundError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("=" * 72)
    print(" HAVENWILD ELIZAWY CLIFF SOURCE-02R2 MULTI-CELL EVIDENCE")
    print("=" * 72)
    print(f"Repository : {repo}")
    print("Runtime    : UNCHANGED")
    print("Worldgen   : UNCHANGED")
    print("Collision  : UNCHANGED")
    print("-" * 72)

    paths = {
        "summer": repo / SUMMER_REL,
        "demo": repo / DEMO_REL,
        "landscape": repo / LANDSCAPE_REL,
    }
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        print("Missing pinned source evidence:\n" + "\n".join(missing), file=sys.stderr)
        return 3

    print("Decoding pinned source/test scenes...")
    source = v1.decode_png(paths["summer"])
    demo = v1.decode_png(paths["demo"])
    landscape = v1.decode_png(paths["landscape"])

    inputs = {
        "summerCliff": verify(paths["summer"], "cliff_summer.png", source),
        "summerDemo": verify(paths["demo"], "DemoGame - 2 - Summer.png", demo),
        "testLandscape": verify(paths["landscape"], "Test Landscape.png", landscape),
    }
    if args.strict_pinned_hashes:
        bad = [
            k for k, rec in inputs.items()
            if not rec["hashMatchesPinned"] or not rec["dimensionsMatchPinned"]
        ]
        if bad:
            print("Pinned input mismatch: " + ", ".join(bad), file=sys.stderr)
            return 4
    print("[PASS] pinned source/test-scene evidence verified")

    stamps = enumerate_stamps()
    print(f"Source-native candidate rectangles: {len(stamps)}")

    # Build one scene color-position index using every source color that may
    # participate in the candidate stamps.
    anchor_colors = candidate_anchor_colors(source, stamps)

    all_scene_data = {}
    artifact_dir = repo / "artifacts/audits/elizawy_cliff_source02r2"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    for scene_name, scene in (
        ("DemoGame - 2 - Summer.png", demo),
        ("Test Landscape.png", landscape),
    ):
        print(f"Scanning multi-cell source stamps in {scene_name}...")
        cache = make_scene_cache(scene, anchor_colors)
        stamp_results = []
        for index, stamp in enumerate(stamps, 1):
            stamp_results.append(match_stamp(source, scene, stamp, cache))
            if index % 250 == 0:
                print(f"  {index}/{len(stamps)} source rectangles evaluated")

        rows = flatten_candidates(scene_name, stamp_results)
        scene_dir = artifact_dir / (
            "demo" if scene_name.startswith("DemoGame") else "landscape"
        )
        scene_dir.mkdir(parents=True, exist_ok=True)
        crops = export_candidates(v1, source, scene, scene_name, rows, scene_dir)
        all_scene_data[scene_name] = {
            "summary": summarize(rows),
            "candidateCount": len(rows),
            "rawStampResults": stamp_results,
            "crops": crops,
        }

    flat_rows = []
    for scene_name, scene_data in all_scene_data.items():
        for result in scene_data["rawStampResults"]:
            for match in result.get("matches", []):
                flat_rows.append({
                    "scene": scene_name,
                    "stamp": result["stamp"],
                    "target": result["target"],
                    "targetRow": result["targetRow"],
                    "sourceRectCells": result["sourceRectCells"],
                    "targetOffsetCells": result["targetOffsetCells"],
                    **match,
                })
    flat_rows.sort(key=lambda r: (-r["rank"], -r["score"]))

    csv_path = artifact_dir / "candidate_index.csv"
    write_csv(csv_path, flat_rows)

    authority = {
        "schema": SCHEMA,
        "pass": PASS_ID,
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "status": "multicell_source_native_evidence_collected",
        "policy": {
            "runtimeRendererChangedByThisPass": False,
            "worldgenChangedByThisPass": False,
            "collisionChangedByThisPass": False,
            "automaticRuntimeCertification": False,
            "sourceAuthority": "ElizaWy/LPC pinned original",
            "transformPolicy": "exact_translation_only_no_rotate_mirror_stretch",
        },
        "inputs": inputs,
        "baselineSource02": {
            "observedC8": [],
            "observedC15": [],
            "reasonForR2": (
                "single-cell matching was under-constrained and dominated by "
                "repeated/ambiguous terrain-color evidence"
            ),
        },
        "matcher": {
            "cellPx": CELL,
            "shapesCells": [list(x) for x in SHAPES],
            "minimumTotalOpaquePixels": MIN_TOTAL_OPAQUE,
            "minimumOccupiedCells": MIN_OCCUPIED_CELLS,
            "minimumCellOpaquePixels": MIN_CELL_OPAQUE,
            "minimumUniqueColors": MIN_UNIQUE_COLORS,
            "sampleThreshold": SAMPLE_THRESHOLD,
            "partialThreshold": PARTIAL_THRESHOLD,
            "strongThreshold": STRONG_THRESHOLD,
            "cellSupportThreshold": CELL_SUPPORT_THRESHOLD,
            "minimumSupportedCells": MIN_SUPPORTED_CELLS,
            "sceneGridAssumed": False,
            "sourceTransformsAllowed": ["translation"],
        },
        "scenes": all_scene_data,
        "candidateCsv": csv_path.relative_to(repo).as_posix(),
        "nextGate": {
            "runtimeCertificationAllowed": False,
            "foreignRampRetirementAllowed": False,
            "required": (
                "Human/source review of exported SOURCE/SCENE pairs. "
                "SOURCE-03 may certify only unambiguous demonstrated assemblies."
            ),
        },
    }

    json_path = artifact_dir / "elizawy_cliff_multicell_assembly_evidence_v2.json"
    md_path = artifact_dir / "HW_CLIFF_SOURCE_02R2_MULTICELL_ASSEMBLY_EVIDENCE.md"
    json_path.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(authority), encoding="utf-8")

    print("-" * 72)
    for scene_name, data in all_scene_data.items():
        print(scene_name)
        for target, summary in data["summary"].items():
            print(
                f"  {target}: {summary['candidateCount']} candidate(s), "
                f"{summary['strongCount']} strong, {summary['partialCount']} partial"
            )
            for best in summary["best"][:3]:
                print(
                    f"    {best['stamp']} score={best['score']} "
                    f"supportedCells={best['supportedCells']} "
                    f"scene=({best['sceneX']},{best['sceneY']})"
                )
    print("Authority :", json_path)
    print("Report    :", md_path)
    print("Index     :", csv_path)
    print("Crops     :", artifact_dir)
    print("[PASS] SOURCE-02R2 evidence audit completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
