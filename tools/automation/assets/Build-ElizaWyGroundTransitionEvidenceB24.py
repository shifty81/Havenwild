#!/usr/bin/env python3
"""B24 source-exact grass/earth/sand transition evidence; never promotes game assets.

Requires B21 evidence, B22 evidence, B23 evidence, and original ElizaWy Terrain.
Reconstructs and authenticates previous preview pixels before writing output.
Pillow is required for explicit review generation only, not the full quality gate.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')
REGIONS = {'grass_on_earth': (6, 0, 3, 3), 'sand_on_earth': (9, 0, 3, 3),
           'warm_sand_motif': (9, 5, 3, 3)}
TILE = 32
B23_SCHEMA = 'havenwild.elizawy_sand_correction_evidence.b23'


def load_neighbor(filename: str, module_name: str):
    path = Path(__file__).with_name(filename)
    if not path.is_file():
        raise ValueError(f'Required preceding pass missing: {path}')
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f'Cannot load preceding pass: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked_json(source, name, schema):
    raw = source.read(name)
    doc = json.loads(raw)
    if doc.get('schema') != schema:
        raise ValueError(f'Invalid {name} schema')
    return doc, raw


def same_image(raw, expected, Image, description):
    actual = Image.open(io.BytesIO(raw)).convert('RGBA')
    actual.load()
    if actual.size != expected.size or actual.tobytes() != expected.tobytes():
        raise ValueError(f'Changed upstream pixels: {description}')


def boundary_samples(image):
    # Corners are counted twice, matching B22/B23's 384-sample convention.
    w, h = image.size
    return ([(x, 0, image.getpixel((x, 0))) for x in range(w)]
            + [(x, h - 1, image.getpixel((x, h - 1))) for x in range(w)]
            + [(0, y, image.getpixel((0, y))) for y in range(h)]
            + [(w - 1, y, image.getpixel((w - 1, y))) for y in range(h)])


def signature(image):
    boundary = boundary_samples(image)
    colors = Counter(value for _, _, value in boundary)
    return {'samples': len(boundary), 'opaque': sum(v[3] == 255 for _, _, v in boundary),
            'colors': [{'rgba': list(color), 'count': count} for color, count in
                       sorted(colors.items(), key=lambda item: item[0])]}


def warm_exceptions(image, pale):
    return [{'pixel': [x, y], 'rgba': list(v)} for x, y, v in boundary_samples(image) if v != pale]


def reconstruct_b23_inputs(args, b, b23, Image):
    upstream = b.Source(args.evidence, 'lpc' if args.evidence.is_file() or
                        (args.evidence / 'lpc').is_dir() else '')
    b22_source = b.Source(args.b22, '')
    b23_source = b.Source(args.b23, '')
    terrain = b.Source(args.terrain, 'Terrain' if args.terrain.is_file() or
                       (args.terrain / 'Terrain').is_dir() else '')
    b21, _ = b.load_b21(upstream)
    b20, _ = checked_json(upstream, 'elizawy_ground_source_regions_b20.json',
                          'havenwild.elizawy_source_region_coverage_generated.b20')
    named = {r['regionId']: r['rectCells'] for r in b20['regions']}
    expected = {
        'summer.01.c.grass_earth_border': REGIONS['grass_on_earth'],
        'summer.01.d.sand_earth_border': REGIONS['sand_on_earth'],
        'summer.03.d.sand_surface_feature': REGIONS['warm_sand_motif'],
    }
    if b20.get('sourceCommit') != b21.get('sourceCommit') or any(
            named.get(k) != list(v) for k,v in expected.items()):
        raise ValueError('B20 named region coordinates changed; no source topology inference')
    b22, b22_bytes = checked_json(b22_source, 'elizawy_ground_landscape_b22.json',
                                  'havenwild.elizawy_ground_landscape_evidence.b22')
    b23_report, raw_b23 = checked_json(b23_source, 'elizawy_sand_correction_b23.json', B23_SCHEMA)
    if b23_report.get('upstreamB22Sha256') != b.sha256(b22_bytes):
        raise ValueError('B23/B22 lineage mismatch')
    for doc in (b22, b23_report):
        if doc.get('previewOnly') is not True:
            raise ValueError('Prior review no longer preview-only')
        for key in ('visualApproval', 'productionApproval', 'runtimeCutover'):
            if doc.get(key) is not False:
                raise ValueError(f'Unexpected promotion flag {key}')
    # Existing B23 reconstructs and authenticates *all* B21 and B22 source PNGs,
    # all five original season SHA values, and the previous report lineage.
    verified = b23.validate_previews(b, upstream, b22_source, terrain, b21, b22, Image)
    if b23_report.get('sourceCommit') != b21.get('sourceCommit'):
        raise ValueError('Source lineage changed since B23')
    if set(b23_report.get('seasons', {})) != set(SEASONS):
        raise ValueError('Incomplete B23 seasonal evidence')
    for season in SEASONS:
        entry = b23_report['seasons'][season]
        if entry.get('originalSourceSha256') != b22['sourceHashes'][f'terrain_{season}.png']:
            raise ValueError(f'B23 source hash changed: {season}')
        if entry.get('grassSandPatchMismatchedPerimeterPixels') != 0 or \
                entry.get('warmMotifStillUnapproved') is not True:
            raise ValueError(f'B23 boundary state changed: {season}')
        original, grass = verified[season]
        pale = b.crop_region(original, (10, 1, 1, 1))
        corrected = b.repeat(pale, 14, 14, Image)
        patch = b.crop_region(original, (6, 5, 3, 3))
        grass_base = b.crop_region(original, (1, 1, 1, 1))
        for x, y in ((2, 2), (9, 7), (3, 10)):
            corrected.alpha_composite(grass_base, dest=((x+1)*TILE, (y+1)*TILE))
            b.paste_original(corrected, patch, x, y)
        same_image(b23_source.read(f'b23_{season}_sand_corrected_source_exact_REVIEW.png'),
                   corrected, Image, f'B23 corrected sand {season}')
        if entry.get('sandReview') != f'b23_{season}_sand_corrected_source_exact_REVIEW.png':
            raise ValueError('B23 review filename binding changed')
    # Verify the B23 metadata itself against a regenerated report. Temporary
    # B23 output is isolated and never modifies an original asset or repo path.
    with tempfile.TemporaryDirectory(prefix='havenwild-b24-upstream-') as tmp:
        regen_args = argparse.Namespace(evidence=args.evidence, b22=args.b22,
                                        terrain=args.terrain, out=Path(tmp))
        rebuilt = b23.run(regen_args)
        if rebuilt != b23_report:
            raise ValueError('B23 metadata differs from authenticated regeneration')
        expected_sheet = Image.open(Path(tmp) / 'B23_all_seasons_sand_correction_review.png').convert('RGBA')
        same_image(b23_source.read('B23_all_seasons_sand_correction_review.png'),
                   expected_sheet, Image, 'B23 full seasonal contact sheet')
    return b21, b22, b23_report, raw_b23, verified


def run(args):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise ValueError('Pillow required for explicit B24 visual review: python -m pip install Pillow') from exc
    b = load_neighbor('Build-ElizaWyGroundLandscapeEvidenceB22.py', 'havenwild_ground_b22')
    b23 = load_neighbor('Build-ElizaWySandCorrectionEvidenceB23.py', 'havenwild_ground_b23')
    output = args.out.resolve()
    for entry in (args.evidence, args.b22, args.b23, args.terrain):
        if entry.is_dir() and (entry.resolve() == output or entry.resolve() in output.parents):
            raise ValueError('Review output cannot be inside source/evidence input')
    b21, b22, prior, raw_b23, sources = reconstruct_b23_inputs(args, b, b23, Image)
    prepared = []
    report = {'schema': 'havenwild.elizawy_ground_transition_evidence.b24',
              'status': 'SOURCE_EXACT_TRANSITION_CROPS_VERIFIED_TOPOLOGY_REVIEW_REQUIRED',
              'sourceProvider': 'elizawy_lpc_revised', 'sourceCommit': b21['sourceCommit'],
              'upstreamB23Sha256': b.sha256(raw_b23), 'previewOnly': True,
              'automatedPixelVerification': True, 'visualApproval': False,
              'semanticApproval': False, 'topologyApproval': False,
              'gameplayApproval': False, 'productionApproval': False,
              'runtimeCutover': False, 'approvedGeneralTransitions': 0,
              'approvedResizes': 0, 'seasons': {},
              'notes': ['Earth borders are two-tone source pixels; treating their entire outer perimeter as a single flat color is an invalid acceptance test.',
                        'Warm sand motif contains exactly 16 authored edge-highlight samples; preserve them rather than recoloring or claiming a seamless tile.',
                        'Exact 3x3 crops demonstrate source roles only; arbitrary shapes, adjacent motif tiling and runtime material transitions are not approved.']}
    for season in SEASONS:
        source, prior_grass = sources[season]
        pale = b.crop_region(source, (10, 1, 1, 1)).getpixel((0, 0))
        warm = b.crop_region(source, (10, 6, 1, 1)).getpixel((0, 0))
        if pale == warm or not b.uniform(b.crop_region(source, (10, 1, 1, 1))):
            raise ValueError(f'Pale/warm source base mismatch: {season}')
        grass_earth = b.crop_region(source, REGIONS['grass_on_earth'])
        sand_earth = b.crop_region(source, REGIONS['sand_on_earth'])
        motif = b.crop_region(source, REGIONS['warm_sand_motif'])
        if grass_earth.crop((TILE, TILE, 2*TILE, 2*TILE)).getbbox() is not None:
            raise ValueError(f'Grass-earth center was modified: {season}')
        if sand_earth.crop((TILE,TILE,2*TILE,2*TILE)).tobytes() != \
                b.crop_region(source, (10, 1, 1, 1)).tobytes():
            raise ValueError(f'Sand-earth center is not original pale sand: {season}')
        # Grass underlay is copied from original source, not invented artwork;
        # exact 3x3 result only (no guessed exterior earth texture or resizing).
        grass_earth_preview = grass_earth.copy()
        grass_center = b.crop_region(source, (1, 1, 1, 1))
        if not b.uniform(grass_center):
            raise ValueError(f'Grass underlay lost uniformity: {season}')
        grass_earth_preview.alpha_composite(grass_center, dest=(TILE, TILE))
        for y in range(3*TILE):
            for x in range(3*TILE):
                if grass_earth.getpixel((x,y))[3] == 255 and \
                        grass_earth_preview.getpixel((x,y)) != grass_earth.getpixel((x,y)):
                    raise ValueError('Modified opaque grass-earth source pixels')
        grass_edge = signature(grass_earth)
        sand_edge = signature(sand_earth)
        if grass_edge['samples'] != 384 or sand_edge['samples'] != 384 or \
                grass_edge['opaque'] != 384 or sand_edge['opaque'] != 384 or \
                len(grass_edge['colors']) != 2 or len(sand_edge['colors']) != 2:
            raise ValueError(f'Authored earth rim signature changed: {season}')
        exceptions = warm_exceptions(motif, pale)
        # Both the RGB value and the coordinates come from original source;
        # B24 diagnoses highlights rather than painting them away.
        if len(exceptions) != 16 or len({tuple(p['rgba']) for p in exceptions}) != 1:
            raise ValueError(f'Warm motif boundary signature changed: {season}')
        if exceptions[0]['rgba'] != list(motif.getpixel((40,0))):
            raise ValueError(f'Warm motif source highlight differs: {season}')
        points = [tuple(p['pixel']) for p in exceptions]
        expected = ([(x,0) for x in range(40,44)] + [(x,0) for x in range(52,56)]
                    + [(95,y) for y in range(40,44)] + [(95,y) for y in range(52,56)])
        if sorted(points) != sorted(expected):
            raise ValueError(f'Warm motif 16 exceptional positions changed: {season}')
        if any(p['rgba'][3] != 255 for p in exceptions):
            raise ValueError('Authored sand boundary lost opacity')
        # Preserve previous grass scene by reading/using authenticated original.
        if prior_grass.size != (24*TILE,14*TILE):
            raise ValueError('B22 grass scene geometry changed')
        filenames = {
            'grassOnEarth': f'b24_{season}_grass_on_earth_SOURCE_EXACT_REVIEW.png',
            'sandOnEarth': f'b24_{season}_sand_on_earth_SOURCE_EXACT_REVIEW.png',
            'warmSandMotif': f'b24_{season}_warm_sand_16_edge_samples_UNAPPROVED.png',
        }
        prepared.append((season, grass_earth_preview, sand_earth, motif, filenames))
        report['seasons'][season] = {
            'sourceSha256': b22['sourceHashes'][f'terrain_{season}.png'],
            'grassEarth': {'rectCells': list(REGIONS['grass_on_earth']), 'centerTransparentInSource': True,
                           'centerUnderlaySourceCell': [1,1], 'sourceOpaquePixelsPreserved': True,
                           'outerBoundary': grass_edge, 'preview': filenames['grassOnEarth']},
            'sandEarth': {'rectCells': list(REGIONS['sand_on_earth']),
                          'centerIsOriginalPaleSand': True, 'sourcePixelsPreserved': True,
                          'outerBoundary': sand_edge, 'preview': filenames['sandOnEarth']},
            'warmMotif': {'rectCells': list(REGIONS['warm_sand_motif']),
                          'paleBaseCell': [10,1], 'warmInteriorCell': [10,6],
                          'unapprovedExceptionalBoundaryPixels': exceptions,
                          'exceptionCount': len(exceptions), 'preview': filenames['warmSandMotif'],
                          'approval': False},
        }
    # All upstream and source diagnostics validated before opening the output.
    output.mkdir(parents=True, exist_ok=True)
    for _, grass, sand, motif, names in prepared:
        for key, img in [('grassOnEarth', grass), ('sandOnEarth', sand), ('warmSandMotif', motif)]:
            img.save(output / names[key])
    panel_w, gap, label_h, season_h = 144, 14, 20, 19
    panel_h = 3*TILE
    row_h = season_h + panel_h + label_h + gap
    sheet = Image.new('RGB', (4*panel_w + 5*gap, len(prepared)*row_h + gap), (29,32,38))
    pen = ImageDraw.Draw(sheet)
    b23_source = b.Source(args.b23, '')
    for row, (season, grass, sand, motif, _) in enumerate(prepared):
        top = gap + row*row_h
        pen.text((gap, top), season.upper(), fill=(255,255,255))
        prior_image = Image.open(io.BytesIO(b23_source.read(
            f'b23_{season}_sand_corrected_source_exact_REVIEW.png'))).convert('RGBA')
        corrected = prior_image.crop((2*TILE,2*TILE,5*TILE,5*TILE))
        for col, (label, img) in enumerate([('GRASS / EARTH',grass), ('SAND / EARTH',sand),
                                           ('WARM: HOLD',motif), ('B23: PALE SAND',corrected)]):
            x = gap + col*(panel_w+gap)
            pen.text((x, top+season_h), label, fill=(240,240,240))
            sheet.paste(img.convert('RGB'), (x + (panel_w-3*TILE)//2, top+season_h+label_h))
    sheet.save(output / 'B24_all_seasons_transition_review.png')
    report['previewCount'] = len(prepared)*3+1
    (output / 'elizawy_ground_transitions_b24.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('evidence','b22','b23','terrain','out'):
        p.add_argument('--'+name, required=True, type=Path)
    args=p.parse_args()
    try:
        result=run(args)
    except (Exception) as exc:
        print(f'B24 FAIL: {exc}', file=sys.stderr)
        return 1
    print('B24 PASS: B21/B22/B23 provenance and prior preview pixels authenticated for 5 seasons.')
    print('B24 PASS: 10 source-exact earth border crops; warm sand has 16 authored edge highlights per season.')
    print(f'B24 REVIEW ONLY: {result["previewCount"]} previews; no material, runtime, or topology approval.')
    print(f'Report: {args.out / "elizawy_ground_transitions_b24.json"}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
