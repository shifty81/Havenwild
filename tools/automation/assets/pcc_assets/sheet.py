from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from .adapters import ProjectAdapter
from .models import (
    AnimationCandidate,
    AssemblyCandidate,
    CellRecord,
    CertificationState,
    GridSpec,
    SeamRecord,
    SheetAnalysis,
)
from .pngio import Image, decode_png
from .provenance import source_record


def infer_grid(image: Image, preferred_w: int = 32, preferred_h: int = 32) -> GridSpec:
    if image.width % preferred_w == 0 and image.height % preferred_h == 0:
        return GridSpec(preferred_w, preferred_h, image.width // preferred_w, image.height // preferred_h)

    common = [8, 16, 24, 32, 48, 64, 96, 128]
    candidates: list[tuple[int, int, int]] = []
    for w in common:
        for h in common:
            if image.width % w == 0 and image.height % h == 0:
                penalty = abs(w - preferred_w) + abs(h - preferred_h)
                candidates.append((penalty, w, h))
    if not candidates:
        raise ValueError(
            f"unable to infer a regular grid for {image.width}x{image.height}; "
            "supply --cell-width/--cell-height"
        )
    _, w, h = min(candidates)
    return GridSpec(w, h, image.width // w, image.height // h)


def _cell_bytes(image: Image, grid: GridSpec, col: int, row: int) -> bytes:
    out = bytearray(grid.cell_width * grid.cell_height * 4)
    pos = 0
    for y in range(row * grid.cell_height, (row + 1) * grid.cell_height):
        start = (y * image.width + col * grid.cell_width) * 4
        chunk = image.rgba[start:start + grid.cell_width * 4]
        out[pos:pos + len(chunk)] = chunk
        pos += len(chunk)
    return bytes(out)


def _alpha_mask(cell_rgba: bytes, threshold: int) -> bytes:
    return bytes(
        1 if cell_rgba[i + 3] >= threshold else 0
        for i in range(0, len(cell_rgba), 4)
    )


def _bbox(mask: bytes, w: int, h: int) -> list[int] | None:
    xs = []
    ys = []
    for i, bit in enumerate(mask):
        if bit:
            xs.append(i % w)
            ys.append(i // w)
    if not xs:
        return None
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def _rgb_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _seam(
    image: Image,
    grid: GridSpec,
    a_col: int,
    a_row: int,
    b_col: int,
    b_row: int,
    direction: str,
    threshold: int,
    min_touch: int,
) -> SeamRecord:
    touching = 0
    continuity = 0
    occupied_positions = 0
    if direction == "E":
        ax = (a_col + 1) * grid.cell_width - 1
        bx = b_col * grid.cell_width
        y0 = a_row * grid.cell_height
        for off in range(grid.cell_height):
            pa = image.pixel(ax, y0 + off)
            pb = image.pixel(bx, y0 + off)
            oa, ob = pa[3] >= threshold, pb[3] >= threshold
            if oa or ob:
                occupied_positions += 1
            if oa and ob:
                touching += 1
                if _rgb_distance(pa, pb) <= 48:
                    continuity += 1
    elif direction == "S":
        ay = (a_row + 1) * grid.cell_height - 1
        by = b_row * grid.cell_height
        x0 = a_col * grid.cell_width
        for off in range(grid.cell_width):
            pa = image.pixel(x0 + off, ay)
            pb = image.pixel(x0 + off, by)
            oa, ob = pa[3] >= threshold, pb[3] >= threshold
            if oa or ob:
                occupied_positions += 1
            if oa and ob:
                touching += 1
                if _rgb_distance(pa, pb) <= 48:
                    continuity += 1
    else:
        raise ValueError(direction)

    score = 0.0 if occupied_positions == 0 else touching / occupied_positions
    connected = touching >= min_touch or score >= 0.20
    return SeamRecord(
        a=f"c{a_col}r{a_row}",
        b=f"c{b_col}r{b_row}",
        direction=direction,
        touching_pixels=touching,
        color_continuity_pixels=continuity,
        occupied_boundary_positions=occupied_positions,
        continuity_score=round(score, 6),
        connected=connected,
    )


def _jaccard(mask_a: bytes, mask_b: bytes) -> float:
    inter = union = 0
    for a, b in zip(mask_a, mask_b):
        if a or b:
            union += 1
        if a and b:
            inter += 1
    return 1.0 if union == 0 else inter / union


def analyze_sheet(
    path: Path,
    adapter: ProjectAdapter,
    cell_width: int | None = None,
    cell_height: int | None = None,
    metadata_evidence: list[dict[str, Any]] | None = None,
) -> SheetAnalysis:
    image = decode_png(path)
    if cell_width and cell_height:
        if image.width % cell_width or image.height % cell_height:
            raise ValueError(
                f"{path} ({image.width}x{image.height}) is not divisible by "
                f"{cell_width}x{cell_height}"
            )
        grid = GridSpec(cell_width, cell_height, image.width // cell_width, image.height // cell_height)
    else:
        grid = infer_grid(image, adapter.default_cell_width, adapter.default_cell_height)

    cells: list[CellRecord] = []
    raw_by_id: dict[str, bytes] = {}
    mask_by_id: dict[str, bytes] = {}
    exact_groups: dict[str, list[str]] = defaultdict(list)
    alpha_groups: dict[str, list[str]] = defaultdict(list)

    for row in range(grid.rows):
        for col in range(grid.columns):
            cid = f"c{col}r{row}"
            raw = _cell_bytes(image, grid, col, row)
            mask = _alpha_mask(raw, adapter.alpha_threshold)
            raw_by_id[cid] = raw
            mask_by_id[cid] = mask
            rh = hashlib.sha256(raw).hexdigest()
            ah = hashlib.sha256(mask).hexdigest()
            exact_groups[rh].append(cid)
            alpha_groups[ah].append(cid)
            occupied = sum(mask)
            cells.append(
                CellRecord(
                    cell_id=cid,
                    column=col,
                    row=row,
                    occupied_pixels=occupied,
                    occupancy_ratio=round(occupied / len(mask), 6),
                    alpha_bbox=_bbox(mask, grid.cell_width, grid.cell_height),
                    rgba_hash=rh,
                    alpha_hash=ah,
                )
            )

    exact_named: dict[str, list[str]] = {}
    alpha_named: dict[str, list[str]] = {}
    exact_id_for_cell: dict[str, str] = {}
    alpha_id_for_cell: dict[str, str] = {}
    eidx = 0
    for _, members in sorted(exact_groups.items()):
        if len(members) > 1:
            gid = f"exact-{eidx:04d}"
            eidx += 1
            exact_named[gid] = members
            for cid in members:
                exact_id_for_cell[cid] = gid
    aidx = 0
    for _, members in sorted(alpha_groups.items()):
        if len(members) > 1:
            gid = f"alpha-{aidx:04d}"
            aidx += 1
            alpha_named[gid] = members
            for cid in members:
                alpha_id_for_cell[cid] = gid

    seams: list[SeamRecord] = []
    graph: dict[str, set[str]] = defaultdict(set)
    for row in range(grid.rows):
        for col in range(grid.columns):
            cid = f"c{col}r{row}"
            if col + 1 < grid.columns:
                s = _seam(image, grid, col, row, col + 1, row, "E", adapter.alpha_threshold, adapter.min_seam_touch_pixels)
                seams.append(s)
                if s.connected:
                    graph[cid].add(s.b)
                    graph[s.b].add(cid)
            if row + 1 < grid.rows:
                s = _seam(image, grid, col, row, col, row + 1, "S", adapter.alpha_threshold, adapter.min_seam_touch_pixels)
                seams.append(s)
                if s.connected:
                    graph[cid].add(s.b)
                    graph[s.b].add(cid)

    cell_lookup = {c.cell_id: c for c in cells}
    occupied_ids = {c.cell_id for c in cells if c.occupied_pixels > 0}
    visited: set[str] = set()
    assemblies: list[AssemblyCandidate] = []
    asm_idx = 0

    for start in sorted(occupied_ids):
        if start in visited:
            continue
        q = deque([start])
        visited.add(start)
        members = []
        while q:
            cur = q.popleft()
            members.append(cur)
            for nxt in graph.get(cur, ()):
                if nxt in occupied_ids and nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        if len(members) < adapter.min_assembly_cells:
            continue

        coords = [(cell_lookup[c].column, cell_lookup[c].row) for c in members]
        min_c = min(c for c, _ in coords)
        max_c = max(c for c, _ in coords)
        min_r = min(r for _, r in coords)
        max_r = max(r for _, r in coords)
        area_cells = (max_c - min_c + 1) * (max_r - min_r + 1)
        occupied_pixels = sum(cell_lookup[c].occupied_pixels for c in members)
        rect_pixels = area_cells * grid.cell_width * grid.cell_height
        seam_count = sum(
            1 for s in seams
            if s.connected and s.a in members and s.b in members
        )
        assembly = AssemblyCandidate(
            assembly_id=f"assembly-{asm_idx:04d}",
            members=sorted(members),
            bounds_cells=[min_c, min_r, max_c - min_c + 1, max_r - min_r + 1],
            footprint=[max_c - min_c + 1, max_r - min_r + 1],
            source_rect_px=[
                min_c * grid.cell_width,
                min_r * grid.cell_height,
                (max_c - min_c + 1) * grid.cell_width,
                (max_r - min_r + 1) * grid.cell_height,
            ],
            seam_count=seam_count,
            occupancy_ratio=round(occupied_pixels / rect_pixels, 6),
            evidence=[{
                "kind": "opaque_seam_connectivity",
                "connectedCellCount": len(members),
                "seamCount": seam_count,
            }],
        )
        assemblies.append(assembly)
        for cid in members:
            cell_lookup[cid].assembly_ids.append(assembly.assembly_id)
        asm_idx += 1

    for c in cells:
        c.exact_duplicate_group = exact_id_for_cell.get(c.cell_id)
        c.alpha_duplicate_group = alpha_id_for_cell.get(c.cell_id)
        if c.occupied_pixels == 0:
            c.classification = "empty"
        elif c.assembly_ids:
            c.classification = "assembly_member_candidate"
        else:
            c.classification = "standalone_candidate"

    # Conservative repeat inference: identical full cells repeated in one column
    # imply a vertical repeat candidate; repeated in one row imply horizontal.
    for asm in assemblies:
        member_set = set(asm.members)
        vertical_repeat = False
        horizontal_repeat = False
        for gid, members in exact_named.items():
            local = [m for m in members if m in member_set]
            if len(local) >= 2:
                coords = [(cell_lookup[m].column, cell_lookup[m].row) for m in local]
                if len({c for c, _ in coords}) == 1:
                    vertical_repeat = True
                if len({r for _, r in coords}) == 1:
                    horizontal_repeat = True
        asm.repeatable_y = vertical_repeat
        asm.repeatable_x = horizontal_repeat

    animations: list[AnimationCandidate] = []
    anim_idx = 0
    # Candidate-only heuristic: 3+ consecutive occupied cells with similar alpha
    # masks and non-identical RGBA. Never runtime-certifies.
    for row in range(grid.rows):
        run: list[str] = []
        for col in range(grid.columns + 1):
            cid = f"c{col}r{row}" if col < grid.columns else None
            occupied = cid is not None and cell_lookup[cid].occupied_pixels > 0
            if occupied:
                run.append(cid)
            else:
                if len(run) >= 3:
                    sims = [
                        _jaccard(mask_by_id[a], mask_by_id[b])
                        for a, b in zip(run, run[1:])
                    ]
                    unique_rgba = len({cell_lookup[x].rgba_hash for x in run})
                    mean = sum(sims) / len(sims)
                    if mean >= 0.70 and unique_rgba > 1:
                        animations.append(AnimationCandidate(
                            candidate_id=f"anim-{anim_idx:04d}",
                            direction="horizontal",
                            frames=list(run),
                            mean_alpha_similarity=round(mean, 6),
                        ))
                        anim_idx += 1
                run = []

    warnings = []
    if grid.cell_width != adapter.default_cell_width or grid.cell_height != adapter.default_cell_height:
        warnings.append(
            f"inferred/declared grid {grid.cell_width}x{grid.cell_height} differs "
            f"from adapter default {adapter.default_cell_width}x{adapter.default_cell_height}"
        )

    return SheetAnalysis(
        schema="pcc.asset.sheet_analysis.v1",
        source=source_record(path),
        grid=grid,
        cells=cells,
        seams=seams,
        assemblies=assemblies,
        animations=animations,
        duplicate_groups={
            "exactRgba": exact_named,
            "alphaMask": alpha_named,
        },
        metadata_evidence=metadata_evidence or [],
        warnings=warnings,
        analyzer={
            "name": "pcc-assets",
            "version": "0.1.0",
            "projectAdapter": adapter.name,
            "automaticRuntimeCertification": False,
            "assemblyMethod": "cell-level opaque seam graph",
            "semanticsInferred": False,
        },
    )
