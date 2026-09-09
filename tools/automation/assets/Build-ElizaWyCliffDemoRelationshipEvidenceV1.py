#!/usr/bin/env python3
"""HW-CLIFF-SOURCE-02: reverse-map official ElizaWy demo scenes to source cells.

No runtime behavior is changed by this tool. It uses only the pinned original
ElizaWy/LPC PNGs already present in Havenwild and produces evidence describing
where source cells are demonstrably used in the official test scenes.

The PNG reader is self-contained and uses only Python's standard library.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import struct
import sys
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "havenwild.worldgen.elizawy_cliff_demo_relationship_evidence.v1"
PASS_ID = "HW-CLIFF-SOURCE-02"

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

SOURCE_MOUNT = Path("assets/source/licensed/lpc_revised")
SUMMER_REL = SOURCE_MOUNT / "Terrain/cliff_summer.png"
DEMO_REL = SOURCE_MOUNT / "_ Test Scenes/DemoGame - 2 - Summer.png"
LANDSCAPE_REL = SOURCE_MOUNT / "_ Test Scenes/Test Landscape.png"

CELL = 32
COLS = 16
ROWS = 14
TARGET_COLUMNS = {8, 15}
TARGET_C8_ROWS = set(range(0, 9))
TARGET_C15_ROWS = set(range(0, 5))

# Deliberately conservative. Evidence below this threshold is recorded as
# unresolved/ambiguous rather than being promoted to an assembly relationship.
MIN_STABLE_PIXELS = 20
SAMPLE_PIXELS = 24
SAMPLE_THRESHOLD = 0.78
FULL_THRESHOLD = 0.965
AMBIGUITY_EPSILON = 0.004
MAX_MATCHES_PER_SOURCE_CELL = 256
MAX_TARGET_WINDOWS = 64


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class Image:
    width: int
    height: int
    rgba: bytes

    def pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        i = (y * self.width + x) * 4
        d = self.rgba
        return d[i], d[i + 1], d[i + 2], d[i + 3]

    def rgb_key(self, x: int, y: int) -> int:
        i = (y * self.width + x) * 4
        d = self.rgba
        return (d[i] << 16) | (d[i + 1] << 8) | d[i + 2]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png(path: Path) -> Image:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"not a PNG: {path}")

    pos = 8
    ihdr = None
    palette = None
    transparency = None
    idat = bytearray()

    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            palette = [
                tuple(chunk[i:i + 3])
                for i in range(0, len(chunk), 3)
            ]
        elif ctype == b"tRNS":
            transparency = bytes(chunk)
        elif ctype == b"IDAT":
            idat.extend(chunk)
        elif ctype == b"IEND":
            break

    if ihdr is None:
        raise ValueError(f"PNG missing IHDR: {path}")

    width, height, bit_depth, color_type, compression, filter_method, interlace = ihdr
    if bit_depth != 8:
        raise ValueError(f"unsupported PNG bit depth {bit_depth}: {path}")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ValueError(
            f"unsupported PNG compression/filter/interlace ({compression},"
            f"{filter_method},{interlace}): {path}"
        )

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"unsupported PNG color type {color_type}: {path}")
    if color_type == 3 and palette is None:
        raise ValueError(f"indexed PNG missing palette: {path}")

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise ValueError(
            f"unexpected decompressed PNG size for {path}: "
            f"{len(raw)} != {expected}"
        )

    scan = bytearray(height * stride)
    src = 0
    for y in range(height):
        f = raw[src]
        src += 1
        row = bytearray(raw[src:src + stride])
        src += stride
        prev_start = (y - 1) * stride
        cur_start = y * stride

        for x in range(stride):
            a = row[x - channels] if x >= channels else 0
            b = scan[prev_start + x] if y > 0 else 0
            c = scan[prev_start + x - channels] if y > 0 and x >= channels else 0
            if f == 0:
                value = row[x]
            elif f == 1:
                value = (row[x] + a) & 0xFF
            elif f == 2:
                value = (row[x] + b) & 0xFF
            elif f == 3:
                value = (row[x] + ((a + b) // 2)) & 0xFF
            elif f == 4:
                value = (row[x] + _paeth(a, b, c)) & 0xFF
            else:
                raise ValueError(f"unsupported PNG filter {f}: {path}")
            scan[cur_start + x] = value

    rgba = bytearray(width * height * 4)
    for y in range(height):
        row = scan[y * stride:(y + 1) * stride]
        for x in range(width):
            si = x * channels
            di = (y * width + x) * 4
            if color_type == 6:
                rgba[di:di + 4] = row[si:si + 4]
            elif color_type == 2:
                rgba[di:di + 3] = row[si:si + 3]
                rgba[di + 3] = 255
            elif color_type == 3:
                idx = row[si]
                r, g, b = palette[idx]
                a = transparency[idx] if transparency is not None and idx < len(transparency) else 255
                rgba[di:di + 4] = bytes((r, g, b, a))
            elif color_type == 0:
                g = row[si]
                rgba[di:di + 4] = bytes((g, g, g, 255))
            elif color_type == 4:
                g, a = row[si], row[si + 1]
                rgba[di:di + 4] = bytes((g, g, g, a))

    return Image(width, height, bytes(rgba))


def encode_png(path: Path, image: Image) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = bytearray()
    stride = image.width * 4
    for y in range(image.height):
        rows.append(0)
        start = y * stride
        rows.extend(image.rgba[start:start + stride])

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)
    ))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(rows), 9)))
    png.extend(chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(png))


def crop(image: Image, x: int, y: int, w: int, h: int) -> Image:
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(image.width, x + w)
    y1 = min(image.height, y + h)
    if x1 <= x0 or y1 <= y0:
        return Image(1, 1, b"\x00\x00\x00\x00")
    out = bytearray((x1 - x0) * (y1 - y0) * 4)
    ow = x1 - x0
    for yy in range(y0, y1):
        src = (yy * image.width + x0) * 4
        dst = ((yy - y0) * ow) * 4
        out[dst:dst + ow * 4] = image.rgba[src:src + ow * 4]
    return Image(ow, y1 - y0, bytes(out))


def source_cell_pixels(source: Image, col: int, row: int) -> list[tuple[int, int, int]]:
    points = []
    x0 = col * CELL
    y0 = row * CELL
    for y in range(CELL):
        for x in range(CELL):
            r, g, b, a = source.pixel(x0 + x, y0 + y)
            if a >= 250:
                points.append((x, y, (r << 16) | (g << 8) | b))
    return points


def image_color_counts(image: Image) -> Counter[int]:
    c: Counter[int] = Counter()
    d = image.rgba
    for i in range(0, len(d), 4):
        if d[i + 3] > 0:
            c[(d[i] << 16) | (d[i + 1] << 8) | d[i + 2]] += 1
    return c


def choose_samples(
    stable: list[tuple[int, int, int]],
    counts: Counter[int],
    limit: int = SAMPLE_PIXELS,
) -> list[tuple[int, int, int]]:
    ordered = sorted(
        stable,
        key=lambda p: (counts.get(p[2], 0), p[1], p[0])
    )
    chosen: list[tuple[int, int, int]] = []
    for p in ordered:
        if not chosen:
            chosen.append(p)
        else:
            # Favor spatially distinct evidence so one tiny decorative cluster
            # cannot generate a false tile match.
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) >= 3 for q in chosen):
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


def build_anchor_positions(image: Image, colors: set[int]) -> dict[int, list[tuple[int, int]]]:
    out = {c: [] for c in colors}
    d = image.rgba
    for y in range(image.height):
        for x in range(image.width):
            i = (y * image.width + x) * 4
            if d[i + 3] == 0:
                continue
            key = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2]
            if key in out:
                out[key].append((x, y))
    return out


def score_at(
    scene: Image,
    left: int,
    top: int,
    points: list[tuple[int, int, int]],
) -> float:
    if not points:
        return 0.0
    hit = 0
    for x, y, rgb in points:
        sx = left + x
        sy = top + y
        if sx < 0 or sy < 0 or sx >= scene.width or sy >= scene.height:
            continue
        if scene.rgb_key(sx, sy) == rgb:
            hit += 1
    return hit / len(points)


def match_source_cells(source: Image, scene: Image) -> dict[str, Any]:
    counts = image_color_counts(scene)

    cells: dict[str, dict[str, Any]] = {}
    anchor_colors: set[int] = set()

    for row in range(ROWS):
        for col in range(COLS):
            stable = source_cell_pixels(source, col, row)
            if len(stable) < MIN_STABLE_PIXELS:
                continue
            samples = choose_samples(stable, counts)
            if not samples:
                continue
            anchor = min(samples, key=lambda p: counts.get(p[2], 0))
            cell_id = f"c{col}r{row}"
            cells[cell_id] = {
                "col": col,
                "row": row,
                "stable": stable,
                "samples": samples,
                "anchor": anchor,
                "anchorSceneFrequency": counts.get(anchor[2], 0),
            }
            anchor_colors.add(anchor[2])

    positions = build_anchor_positions(scene, anchor_colors)
    matches_by_cell: dict[str, list[dict[str, Any]]] = {}

    for cell_id, info in cells.items():
        ax, ay, color = info["anchor"]
        candidates = positions.get(color, [])
        found: list[dict[str, Any]] = []
        seen = set()
        for px, py in candidates:
            left = px - ax
            top = py - ay
            if (left, top) in seen:
                continue
            seen.add((left, top))
            if left < 0 or top < 0 or left + CELL > scene.width or top + CELL > scene.height:
                continue
            sample_score = score_at(scene, left, top, info["samples"])
            if sample_score < SAMPLE_THRESHOLD:
                continue
            full_score = score_at(scene, left, top, info["stable"])
            if full_score >= FULL_THRESHOLD:
                found.append({
                    "x": left,
                    "y": top,
                    "score": round(full_score, 6),
                    "sampleScore": round(sample_score, 6),
                    "stablePixels": len(info["stable"]),
                })
        found.sort(key=lambda m: (-m["score"], m["y"], m["x"]))
        matches_by_cell[cell_id] = found[:MAX_MATCHES_PER_SOURCE_CELL]

    # Resolve one best source identity per scene top-left. Ambiguous identities
    # remain explicit and are excluded from adjacency certification.
    by_position: dict[tuple[int, int], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for cell_id, matches in matches_by_cell.items():
        for m in matches:
            by_position[(m["x"], m["y"])].append((cell_id, m))

    resolved: dict[tuple[int, int], dict[str, Any]] = {}
    ambiguous: list[dict[str, Any]] = []
    for pos, options in by_position.items():
        options.sort(
            key=lambda item: (
                -item[1]["score"],
                -item[1]["stablePixels"],
                item[0]
            )
        )
        best_id, best = options[0]
        if len(options) > 1 and abs(best["score"] - options[1][1]["score"]) <= AMBIGUITY_EPSILON:
            ambiguous.append({
                "x": pos[0],
                "y": pos[1],
                "options": [
                    {"cell": cid, "score": m["score"], "stablePixels": m["stablePixels"]}
                    for cid, m in options[:8]
                ],
            })
            continue
        resolved[pos] = {
            "cell": best_id,
            "score": best["score"],
            "stablePixels": best["stablePixels"],
        }

    adjacency: dict[str, Counter[str]] = defaultdict(Counter)
    directions = {
        "N": (0, -CELL),
        "E": (CELL, 0),
        "S": (0, CELL),
        "W": (-CELL, 0),
    }
    for (x, y), rec in resolved.items():
        for direction, (dx, dy) in directions.items():
            other = resolved.get((x + dx, y + dy))
            if other:
                adjacency[f"{rec['cell']}:{direction}"][other["cell"]] += 1

    return {
        "matchesByCell": matches_by_cell,
        "resolved": resolved,
        "ambiguous": ambiguous,
        "adjacency": adjacency,
    }


def target_evidence(scene_name: str, match_result: dict[str, Any]) -> dict[str, Any]:
    resolved: dict[tuple[int, int], dict[str, Any]] = match_result["resolved"]
    adj = match_result["adjacency"]
    out = []

    for (x, y), rec in sorted(resolved.items(), key=lambda item: (item[0][1], item[0][0])):
        cell = rec["cell"]
        if not (
            cell.startswith("c8r")
            or cell.startswith("c15r")
        ):
            continue
        try:
            col = int(cell[1:cell.index("r")])
            row = int(cell[cell.index("r") + 1:])
        except ValueError:
            continue
        if col == 8 and row not in TARGET_C8_ROWS:
            continue
        if col == 15 and row not in TARGET_C15_ROWS:
            continue

        neighbors = {}
        for direction in ("N", "E", "S", "W"):
            dx, dy = {"N": (0, -CELL), "E": (CELL, 0), "S": (0, CELL), "W": (-CELL, 0)}[direction]
            other = resolved.get((x + dx, y + dy))
            neighbors[direction] = other["cell"] if other else None

        # 5x5 tile neighborhood matrix centered on the observed target.
        matrix = []
        for gy in range(-2, 3):
            row_cells = []
            for gx in range(-2, 3):
                other = resolved.get((x + gx * CELL, y + gy * CELL))
                row_cells.append(other["cell"] if other else None)
            matrix.append(row_cells)

        out.append({
            "scene": scene_name,
            "cell": cell,
            "x": x,
            "y": y,
            "score": rec["score"],
            "neighbors": neighbors,
            "window5x5": matrix,
        })

    # Aggregate actual observed adjacency counts for target roles.
    aggregate = {}
    for key, counter in adj.items():
        cell, direction = key.split(":", 1)
        if not (cell.startswith("c8r") or cell.startswith("c15r")):
            continue
        aggregate[key] = dict(counter.most_common())

    return {
        "observations": out[:MAX_TARGET_WINDOWS],
        "adjacencyCounts": aggregate,
    }


def connected_target_components(match_result: dict[str, Any]) -> list[dict[str, Any]]:
    resolved: dict[tuple[int, int], dict[str, Any]] = match_result["resolved"]
    unvisited = set(resolved)
    components = []

    while unvisited:
        start = next(iter(unvisited))
        q = deque([start])
        unvisited.remove(start)
        points = []
        has_target = False

        while q:
            p = q.popleft()
            rec = resolved[p]
            points.append((p, rec))
            cell = rec["cell"]
            if cell.startswith("c8r") or cell.startswith("c15r"):
                has_target = True
            x, y = p
            for dx, dy in ((CELL, 0), (-CELL, 0), (0, CELL), (0, -CELL)):
                np = (x + dx, y + dy)
                if np in unvisited:
                    unvisited.remove(np)
                    q.append(np)

        if not has_target:
            continue

        xs = [p[0][0] for p in points]
        ys = [p[0][1] for p in points]
        entries = [
            {
                "x": pos[0],
                "y": pos[1],
                "cell": rec["cell"],
                "score": rec["score"],
            }
            for pos, rec in sorted(points, key=lambda item: (item[0][1], item[0][0]))
        ]
        components.append({
            "boundsPx": [
                min(xs),
                min(ys),
                max(xs) - min(xs) + CELL,
                max(ys) - min(ys) + CELL,
            ],
            "tileCount": len(points),
            "entries": entries,
        })

    components.sort(key=lambda c: (-c["tileCount"], c["boundsPx"][1], c["boundsPx"][0]))
    return components[:64]


def crop_target_evidence(
    image: Image,
    scene_name: str,
    evidence: dict[str, Any],
    output_dir: Path,
) -> list[str]:
    written = []
    safe_scene = scene_name.replace(" ", "_").replace("/", "_")
    for idx, obs in enumerate(evidence["observations"][:16]):
        x = obs["x"] - CELL * 2
        y = obs["y"] - CELL * 2
        c = crop(image, x, y, CELL * 5, CELL * 5)
        filename = f"{safe_scene}_{idx:02d}_{obs['cell']}_context.png"
        path = output_dir / filename
        encode_png(path, c)
        written.append(filename)
    return written


def locate_required(repo: Path) -> dict[str, Path]:
    required = {
        "summer": repo / SUMMER_REL,
        "demo": repo / DEMO_REL,
        "landscape": repo / LANDSCAPE_REL,
    }
    missing = [str(p) for p in required.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing required pinned ElizaWy evidence:\n" + "\n".join(missing))
    return required


def verify_input(name: str, path: Path, image: Image) -> dict[str, Any]:
    expected = EXPECTED[name]
    digest = sha256(path)
    dims = [image.width, image.height]
    return {
        "path": path.as_posix(),
        "sha256": digest,
        "dimensions": dims,
        "hashMatchesPinnedAudit": digest == expected["sha256"],
        "dimensionsMatchPinnedAudit": dims == expected["dimensions"],
    }


def serialize_match_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "matchedSourceCellCount": sum(1 for v in result["matchesByCell"].values() if v),
        "resolvedSceneTileCount": len(result["resolved"]),
        "ambiguousSceneTileCount": len(result["ambiguous"]),
        "sourceCellMatchCounts": {
            k: len(v) for k, v in sorted(result["matchesByCell"].items())
            if v
        },
        "ambiguousPositions": result["ambiguous"][:256],
    }


def determine_status(targets: list[dict[str, Any]]) -> dict[str, Any]:
    cells = Counter()
    for t in targets:
        for obs in t["observations"]:
            cells[obs["cell"]] += 1
    c8_observed = sorted(c for c in cells if c.startswith("c8r"))
    c15_observed = sorted(c for c in cells if c.startswith("c15r"))
    return {
        "c8ObservedCells": c8_observed,
        "c15ObservedCells": c15_observed,
        "sideEntryEvidenceState": (
            "demo_relationship_evidence_present"
            if any(c in c8_observed for c in ("c8r3", "c8r4", "c8r5"))
            else "unresolved_no_high_confidence_demo_match"
        ),
        "rightTerminalEvidenceState": (
            "demo_relationship_evidence_present"
            if c15_observed
            else "unresolved_no_high_confidence_demo_match"
        ),
        "runtimeCertificationAllowed": False,
        "foreignRampRetirementAllowed": False,
        "reason": (
            "SOURCE-02 records demonstrated relationships only. Runtime promotion "
            "requires human/source review of the observed assemblies and, where "
            "available, TSX donor cross-checking."
        ),
    }


def markdown(authority: dict[str, Any]) -> str:
    status = authority["evidenceStatus"]
    lines = [
        "# HW-CLIFF-SOURCE-02 — Official Demo Relationship Evidence",
        "",
        "This pass is **evidence only**. It changes no runtime renderer, worldgen, collision, or traversal code.",
        "",
        "## Pinned source verification",
        "",
    ]
    for key, rec in authority["inputs"].items():
        lines.append(
            f"- **{key}**: hash={rec['hashMatchesPinnedAudit']} "
            f"dimensions={rec['dimensionsMatchPinnedAudit']} — `{rec['path']}`"
        )
    lines += [
        "",
        "## Source-native evidence status",
        "",
        f"- c8 cells observed in official scenes: `{', '.join(status['c8ObservedCells']) or 'none'}`",
        f"- c15 cells observed in official scenes: `{', '.join(status['c15ObservedCells']) or 'none'}`",
        f"- side-entry state: **{status['sideEntryEvidenceState']}**",
        f"- right-terminal state: **{status['rightTerminalEvidenceState']}**",
        "- runtime certification allowed: **False**",
        "- foreign ramp retirement allowed: **False**",
        "",
        "## Method",
        "",
        "1. Decode the original pinned PNGs with a standard-library-only decoder.",
        "2. Use only fully opaque source pixels as stable evidence.",
        "3. Find source-cell occurrences at arbitrary scene pixel offsets; no 32px scene-grid assumption.",
        "4. Resolve high-confidence cell identities and preserve ambiguous matches separately.",
        "5. Record observed N/E/S/W source-cell adjacency.",
        "6. Extract connected demo components containing c8/c15 evidence.",
        "7. Export 5×5 visual context crops under `artifacts/audits/elizawy_cliff_source02/`.",
        "",
        "## Important",
        "",
        "A demonstrated match is evidence of source usage, **not** automatic runtime certification.",
        "SOURCE-03 may promote an assembly only after reviewing the exact observed neighborhood and any available Tiled/TSX relationship evidence.",
        "",
    ]
    for scene_name, scene in authority["scenes"].items():
        lines += [
            f"## {scene_name}",
            "",
            f"- matched source cells: {scene['summary']['matchedSourceCellCount']}",
            f"- resolved scene positions: {scene['summary']['resolvedSceneTileCount']}",
            f"- ambiguous positions retained: {scene['summary']['ambiguousSceneTileCount']}",
            f"- target observations: {len(scene['targets']['observations'])}",
            f"- connected target components: {len(scene['targetComponents'])}",
            "",
        ]
    return "\n".join(lines)


def discover_repo_root(explicit: Path | None) -> Path:
    """Resolve Havenwild without requiring command-line arguments.

    The installed script lives at:
      <repo>/tools/automation/assets/Build-ElizaWyCliffDemoRelationshipEvidenceV1.py

    We prefer that structural relationship, then fall back to the current
    directory and the two historical Desktop checkout names.
    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)

    script_path = Path(__file__).resolve()
    if len(script_path.parents) >= 4:
        candidates.append(script_path.parents[3])

    candidates.extend([
        Path.cwd(),
        Path.home() / "Desktop" / "Havenwild-main",
        Path.home() / "Desktop" / "Havenwild",
    ])

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if (
            (resolved / "Cargo.toml").is_file()
            and (resolved / "crates/haven_game").is_dir()
            and (resolved / SOURCE_MOUNT).is_dir()
        ):
            return resolved

    searched = "\n".join(f"  - {p}" for p in candidates)
    raise FileNotFoundError(
        "Could not locate the Havenwild repository automatically. "
        "Use --repo-root <path> if this checkout has a non-standard layout.\n"
        f"Searched:\n{searched}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        help=(
            "Havenwild repository root. Optional when the tool is installed "
            "under <repo>/tools/automation/assets."
        ),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-report", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--strict-pinned-hashes", action="store_true")
    args = parser.parse_args()

    try:
        repo = discover_repo_root(args.repo_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Repository: {repo}")
    paths = locate_required(repo)

    print("HW-CLIFF-SOURCE-02")
    print("Decoding pinned ElizaWy PNG evidence...")

    source = decode_png(paths["summer"])
    demo = decode_png(paths["demo"])
    landscape = decode_png(paths["landscape"])

    inputs = {
        "summerCliff": verify_input("cliff_summer.png", paths["summer"], source),
        "summerDemo": verify_input("DemoGame - 2 - Summer.png", paths["demo"], demo),
        "testLandscape": verify_input("Test Landscape.png", paths["landscape"], landscape),
    }

    if args.strict_pinned_hashes:
        bad = [
            key for key, rec in inputs.items()
            if not rec["hashMatchesPinnedAudit"] or not rec["dimensionsMatchPinnedAudit"]
        ]
        if bad:
            print("Pinned evidence mismatch:", ", ".join(bad), file=sys.stderr)
            return 4

    print("Matching original source cells into DemoGame - 2 - Summer.png...")
    demo_result = match_source_cells(source, demo)
    demo_targets = target_evidence("DemoGame - 2 - Summer.png", demo_result)
    demo_components = connected_target_components(demo_result)

    print("Matching original source cells into Test Landscape.png...")
    landscape_result = match_source_cells(source, landscape)
    landscape_targets = target_evidence("Test Landscape.png", landscape_result)
    landscape_components = connected_target_components(landscape_result)

    artifact_dir = args.artifact_dir or (
        repo / "artifacts/audits/elizawy_cliff_source02"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    demo_crops = crop_target_evidence(
        demo, "DemoGame - 2 - Summer", demo_targets, artifact_dir
    )
    landscape_crops = crop_target_evidence(
        landscape, "Test Landscape", landscape_targets, artifact_dir
    )

    authority = {
        "schema": SCHEMA,
        "pass": PASS_ID,
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "status": "official_demo_relationship_evidence_collected",
        "policy": {
            "runtimeRendererChangedByThisPass": False,
            "worldgenChangedByThisPass": False,
            "collisionChangedByThisPass": False,
            "automaticRuntimePromotion": False,
            "sourceArtAuthority": "ElizaWy/LPC pinned source",
            "rule": (
                "Observed scene adjacency is evidence. It is not a license to "
                "invent transforms, substitute another cliff family, or infer "
                "a ramp footprint that is not demonstrated."
            ),
        },
        "inputs": inputs,
        "matcher": {
            "cellPx": CELL,
            "minimumStableOpaquePixels": MIN_STABLE_PIXELS,
            "samplePixels": SAMPLE_PIXELS,
            "sampleThreshold": SAMPLE_THRESHOLD,
            "fullThreshold": FULL_THRESHOLD,
            "ambiguityEpsilon": AMBIGUITY_EPSILON,
            "sceneGridAssumed": False,
            "opaqueMaskOnly": True,
        },
        "scenes": {
            "DemoGame - 2 - Summer.png": {
                "summary": serialize_match_summary(demo_result),
                "targets": demo_targets,
                "targetComponents": demo_components,
                "contextCrops": demo_crops,
            },
            "Test Landscape.png": {
                "summary": serialize_match_summary(landscape_result),
                "targets": landscape_targets,
                "targetComponents": landscape_components,
                "contextCrops": landscape_crops,
            },
        },
        "evidenceStatus": determine_status([demo_targets, landscape_targets]),
        "next": [
            "Review c8 target observations and connected components against the official source sheet.",
            "Review c15 terminal observations and demonstrated neighbors.",
            "If Tiled donor becomes available, cross-check Wang/terrain relationships against these demo observations.",
            "Write source-native assembly candidates with exact source cells, footprint, anchor, valid adjacency and evidence references.",
            "Only SOURCE-03 may decide whether any assembly is sufficiently proven for runtime certification.",
        ],
    }

    output_json = args.output_json or (
        repo / "artifacts/audits/elizawy_cliff_demo_relationship_evidence_v1.json"
    )
    output_report = args.output_report or (
        repo / "artifacts/audits/HW_CLIFF_SOURCE_02_DEMO_RELATIONSHIP_EVIDENCE.md"
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
    output_report.write_text(markdown(authority), encoding="utf-8")

    print(f"Authority : {output_json}")
    print(f"Report    : {output_report}")
    print(f"Crops     : {artifact_dir}")
    print("c8        :", ", ".join(authority["evidenceStatus"]["c8ObservedCells"]) or "none")
    print("c15       :", ", ".join(authority["evidenceStatus"]["c15ObservedCells"]) or "none")
    print("Status    :", authority["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
