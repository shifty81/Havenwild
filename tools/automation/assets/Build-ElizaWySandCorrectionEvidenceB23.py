#!/usr/bin/env python3
"""B23: non-promoting, source-exact review of corrected ElizaWy pale sand composition.

Read-only access to original source and existing B21/B22 evidence; output evidence
only. Depends on the B22 evidence generator for shared source/pixel validation.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path

SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')
PALE_SAND_CELL = (10, 1)
WARM_SAND_CELL = (10, 6)
AUTHORED_GRASS_ON_SAND = (6, 5, 3, 3)
WARM_SAND_MOTIF = (9, 5, 3, 3)
TILE = 32


def b22_module():
    """Reuse B22 verification without copying or changing its existing code."""
    file = Path(__file__).with_name('Build-ElizaWyGroundLandscapeEvidenceB22.py')
    if not file.is_file():
        raise RuntimeError(f'Required B22 source generator is missing: {file}')
    spec = importlib.util.spec_from_file_location('havenwild_b22_evidence', file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load existing B22 evidence generator: {file}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_report(source, filename: str, expected_schema: str):
    raw = source.read(filename)
    report = json.loads(raw)
    if report.get('schema') != expected_schema:
        raise ValueError(f'Unexpected evidence schema: {filename}')
    return report, raw


def validate_previews(b, b21_source, b22_source, terrain_source, b21, b22_report, Image):
    """Fail closed: validate all upstream hashes and reconstruct both B22 examples."""
    b21_raw = b21_source.read(b.B21_NAME)
    if b.sha256(b21_raw) != b22_report.get('b21Sha256'):
        raise ValueError('B22 B21 evidence hash mismatch')
    surfaces = {r['surfaceId']: r for r in b21['surfaces']}
    if set(surfaces) != {'ground.grass.base', 'ground.sand.base', 'ground.water.base.visual'}:
        raise ValueError('Unexpected B21 ground surface set')
    if surfaces['ground.grass.base']['sourceCell'] != [1, 1]:
        raise ValueError('B21 grass cell changed; B22 reconstruction unsafe')
    if surfaces['ground.sand.base']['sourceCell'] != list(WARM_SAND_CELL):
        raise ValueError('B21 warm sand source coordinate changed; audit baseline')
    verified = {}
    for season in SEASONS:
        name = f'terrain_{season}.png'
        raw, source = b.source_image(terrain_source, name, Image)
        if b.sha256(raw) != b22_report['sourceHashes'].get(name):
            raise ValueError(f'Original season source mismatch: {name}')
        for surface in surfaces.values():
            bind = surface['seasonBindings'][season]
            if bind['sourcePath'] != f'Terrain/{name}' or bind['sourceSha256'] != b.sha256(raw):
                raise ValueError(f'B21 source binding changed for {name}')
        b.verify_b21_previews(b21_source, season, source, surfaces, Image)
        grass = b.repeat(b.crop_region(source, (1, 1, 1, 1)), 24, 14, Image)
        for kind, x, y in [('grass_tuft', 2, 2), ('grass_pool', 9, 3),
                            ('grass_tuft', 18, 8), ('grass_pool', 4, 9)]:
            b.paste_original(grass, b.crop_region(source, b.REGIONS[kind]), x, y)
        prior_grass = Image.open(io.BytesIO(b22_source.read(f'b22_{season}_grass_pond_authored_only.png'))).convert('RGBA')
        prior_grass.load()
        if prior_grass.size != grass.size or prior_grass.tobytes() != grass.tobytes():
            raise ValueError(f'B22 grass/pond evidence altered: {season}')
        prior_sand = b.repeat(b.crop_region(source, (*WARM_SAND_CELL, 1, 1)), 12, 10, Image)
        b.paste_original(prior_sand, b.crop_region(source, WARM_SAND_MOTIF), 4, 3)
        supplied_sand = Image.open(io.BytesIO(b22_source.read(f'b22_{season}_sand_isolated_UNAPPROVED.png'))).convert('RGBA')
        supplied_sand.load()
        if supplied_sand.size != prior_sand.size or supplied_sand.tobytes() != prior_sand.tobytes():
            raise ValueError(f'B22 rejected sand diagnostic altered: {season}')
        verified[season] = (source, grass)
    return verified


def exact_perimeter_mismatch(crop, plain_rgba):
    """Compare every outer pixel against a constant underlay (corners counted twice)."""
    w, h = crop.size
    pixels = crop.load()
    return (sum(pixels[x, y] != plain_rgba for x in range(w) for y in (0, h - 1))
            + sum(pixels[x, y] != plain_rgba for y in range(h) for x in (0, w - 1)))


def run(args):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError('Pillow required for optional B23 visual evidence: python -m pip install Pillow') from exc
    b = b22_module()
    b21_source = b.Source(args.evidence, 'lpc' if args.evidence.is_file() or (args.evidence / 'lpc').is_dir() else '')
    b22_source = b.Source(args.b22, '')
    terrain_source = b.Source(args.terrain, 'Terrain' if args.terrain.is_file() or (args.terrain / 'Terrain').is_dir() else '')
    out = args.out.resolve()
    for candidate in (args.evidence, args.b22, args.terrain):
        if candidate.is_dir() and (out == candidate.resolve() or candidate.resolve() in out.parents):
            raise ValueError('Output must not be inside an original source or evidence directory')
    b21, _ = b.load_b21(b21_source)
    b22, b22_raw = read_report(b22_source, 'elizawy_ground_landscape_b22.json',
                               'havenwild.elizawy_ground_landscape_evidence.b22')
    for flag in ('previewOnly',):
        if b22.get(flag) is not True:
            raise ValueError('Unexpected B22 preview state')
    for flag in ('visualApproval', 'topologyApproval', 'gameplayApproval', 'productionApproval', 'runtimeCutover'):
        if b22.get(flag) is not False:
            raise ValueError('Unexpected B22 approval state; stop and audit')
    if b22.get('sourceCommit') != b21.get('sourceCommit') or b22.get('automatedPixelVerification') is not True:
        raise ValueError('B22/B21 source lineage or pixel check invalid')
    inputs = validate_previews(b, b21_source, b22_source, terrain_source, b21, b22, Image)
    report = {
        'schema': 'havenwild.elizawy_sand_correction_evidence.b23',
        'status': 'SOURCE_EXACT_BOUNDARY_CORRECTED_PREVIEW_VISUAL_REVIEW_REQUIRED',
        'sourceProvider': 'elizawy_lpc_revised',
        'sourceCommit': b21['sourceCommit'],
        'upstreamB22Sha256': b.sha256(b22_raw),
        'b21SandCellUnmodified': list(WARM_SAND_CELL),
        'proposedCorrectedSandBase': {'sourceCell': list(PALE_SAND_CELL), 'sourceRole': 'pale_sand_exterior_candidate',
                                      'previewOnly': True, 'semanticApproval': False},
        'warmSandCellRole': {'sourceCell': list(WARM_SAND_CELL), 'sourceRole': 'warm_sand_interior_candidate',
                             'semanticApproval': False},
        'sourceGrassSandPatch': {'sourceRectCells': list(AUTHORED_GRASS_ON_SAND), 'unmodified': True,
                                  'noResize': True, 'centerUnderlaySourceCell': [1, 1], 'paintApproval': False},
        'previewOnly': True,
        'automatedPixelVerification': True,
        'visualApproval': False,
        'semanticApproval': False,
        'topologyApproval': False,
        'gameplayApproval': False,
        'productionApproval': False,
        'runtimeCutover': False,
        'approvedExternalTransitions': 0,
        'approvedResizes': 0,
        'remainingWork': ['Human visual review at native pixel scale',
                          'Generalized earth/grass/sand boundaries and shoreline topology',
                          'Gameplay material bindings and editor–client PIE parity'],
        'seasons': {},
    }
    # All sources, B21, and B22 verified BEFORE creating output files.
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for season, (source, grass) in inputs.items():
        pale = b.crop_region(source, (*PALE_SAND_CELL, 1, 1))
        warm = b.crop_region(source, (*WARM_SAND_CELL, 1, 1))
        pale_rgba = pale.getpixel((0, 0))
        warm_rgba = warm.getpixel((0, 0))
        if not b.uniform(pale) or pale_rgba[3] != 255 or pale_rgba == warm_rgba:
            raise ValueError(f'Pale sand candidate invalid: {season}')
        if not b.uniform(warm) or warm_rgba[3] != 255:
            raise ValueError(f'B21 warm sand changed: {season}')
        patch = b.crop_region(source, AUTHORED_GRASS_ON_SAND)
        if exact_perimeter_mismatch(patch, pale_rgba):
            raise ValueError(f'Authored grass-on-sand perimeter mismatch: {season}')
        if patch.getpixel((TILE + 16, 16)) == pale_rgba:
            raise ValueError(f'Authored sand patch no longer contains grass feature: {season}')
        warm_motif = b.crop_region(source, WARM_SAND_MOTIF)
        old_mismatch = exact_perimeter_mismatch(warm_motif, warm_rgba)
        corrected_mismatch = exact_perimeter_mismatch(warm_motif, pale_rgba)
        if old_mismatch <= corrected_mismatch or corrected_mismatch != 16:
            raise ValueError(f'Sand motif boundary signature changed: {season}; manually re-audit')
        grass_underlay = b.crop_region(source, (1, 1, 1, 1))
        if not b.uniform(grass_underlay) or grass_underlay.getpixel((0, 0))[3] != 255:
            raise ValueError(f'Original grass center underlay invalid: {season}')
        # Authored 3x3 patch has one fully transparent CENTER CELL. Fill that
        # cell with the original season's grass tile BEFORE source composition;
        # sand remains its exact authored pale exterior, no new art is drawn.
        center_tile = patch.crop((TILE, TILE, 2*TILE, 2*TILE))
        if center_tile.getbbox() is not None:
            raise ValueError(f'Grass/sand patch center must be transparent: {season}')
        sand = b.repeat(pale, 14, 14, Image)
        placements = [(2, 2), (9, 7), (3, 10)]
        for x, y in placements:
            sand.alpha_composite(grass_underlay, dest=((x+1)*TILE, (y+1)*TILE))
            b.paste_original(sand, patch, x, y)
            placed = sand.crop((x*TILE, y*TILE, (x+3)*TILE, (y+3)*TILE))
            original = patch.load(); sampled = placed.load()
            for py in range(3*TILE):
                for px in range(3*TILE):
                    if original[px, py][3] == 255 and sampled[px, py] != original[px, py]:
                        raise ValueError(f'Original sand-grass source pixels mutated: {season}')
            if exact_perimeter_mismatch(placed, pale_rgba):
                raise ValueError(f'Composited patch boundary mismatched: {season}')
            if placed.crop((TILE,TILE,2*TILE,2*TILE)).tobytes() != grass_underlay.tobytes():
                raise ValueError(f'Authentic grass center was not preserved: {season}')
        filename = f'b23_{season}_sand_corrected_source_exact_REVIEW.png'
        sand.save(out / filename)
        rows.append((season, grass, sand))
        report['seasons'][season] = {
            'originalSourceSha256': b22['sourceHashes'][f'terrain_{season}.png'],
            'paleBasePixelRepeatVerified': True,
            'grassSandPatchExactBoundaryPixels': 384,
            'grassSandPatchMismatchedPerimeterPixels': 0,
            'patchPlacements': [list(q) for q in placements],
            'patchSourceOpaquePixelsPreserved': True,
            'sourceGrassCenterCellExact': True,
            'rejectedWarmMotifMismatchOnB21WarmBase': old_mismatch,
            'warmMotifMismatchOnPaleBase': corrected_mismatch,
            'warmMotifStillUnapproved': True,
            'sandReview': filename,
        }
    # Contact labels are outside unchanged scene pixels; no scaling or antialiasing.
    margin, label_h, gap = 18, 26, 12
    left_w, right_w = 24*TILE, 14*TILE
    row_h = 14*TILE+label_h+gap
    sheet = Image.new('RGB', (left_w+right_w+3*margin, len(rows)*row_h+margin), (29, 32, 38))
    draw = ImageDraw.Draw(sheet)
    for i, (season, grass, sand) in enumerate(rows):
        y = margin+i*row_h
        draw.text((margin, y), f'{season.upper()} / B22 GRASS + POND UNCHANGED', fill=(240, 240, 240))
        draw.text((2*margin+left_w, y), 'B23 PALE SAND + AUTHORED GRASS / REVIEW', fill=(240, 240, 240))
        sheet.paste(grass.convert('RGB'), (margin, y+label_h))
        sheet.paste(sand.convert('RGB'), (2*margin+left_w, y+label_h))
    sheet.save(out/'B23_all_seasons_sand_correction_review.png')
    report['previewCount'] = len(rows)+1
    (out/'elizawy_sand_correction_b23.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True, help='Original B21 lpc(5).zip or extracted folder')
    p.add_argument('--b22', type=Path, required=True, help='Unmodified B22 generated evidence ZIP or folder')
    p.add_argument('--terrain', type=Path, required=True, help='Original ElizaWy Terrain.zip or extracted folder')
    p.add_argument('--out', type=Path, required=True, help='Output folder for preview evidence only')
    args = p.parse_args()
    try:
        report = run(args)
    except (Exception) as exc:
        print(f'B23 FAIL: {exc}', file=sys.stderr)
        return 1
    print('B23 PASS: original B21/B22 images and source SHA authenticated across five seasons.')
    print('B23 PASS: pale sand source (10,1); grass-on-sand (6,5) 384/384 matching perimeter pixels each season.')
    print('B23 DIAGNOSTIC: original warm-sand motif mismatch 384 -> 16 on corrected base; motif remains unapproved.')
    print(f'B23 REVIEW ONLY: {report["previewCount"]} images; zero runtime, gameplay, or topology approvals.')
    print(f'Evidence: {args.out / "elizawy_sand_correction_b23.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
