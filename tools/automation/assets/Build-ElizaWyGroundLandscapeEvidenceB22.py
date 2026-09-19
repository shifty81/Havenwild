#!/usr/bin/env python3
"""B22: non-promoting ElizaWy terrain landscape visual evidence.

Inputs are the pre-existing B21 evidence and ORIGINAL ElizaWy Terrain files.
No source assets or runtime files are changed. Pillow is only needed for this
optional image-review tool, never as a hidden full-quality-gate dependency.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

SEASONS = ('spring', 'summer', 'autumn', 'winter', 'winter_ice')
TILE = 32
REGIONS = {
    'grass_tuft': (0, 0, 3, 3),
    'grass_pool': (0, 10, 3, 3),
    'sand_feature': (9, 5, 3, 3),
}
B21_NAME = 'elizawy_ground_composition_b21.json'


class EvidenceError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Source:
    """Read exact named inputs from a ZIP or a folder, without unpacking paths."""

    def __init__(self, location: Path, prefix: str):
        self.path = location
        self.prefix = prefix
        if not location.is_dir() and not (location.is_file() and zipfile.is_zipfile(location)):
            raise EvidenceError(f'Not a directory or ZIP: {location}')

    def read(self, name: str) -> bytes:
        if name.startswith('/') or '..' in Path(name).parts:
            raise EvidenceError('Unsafe source member name')
        rel = f'{self.prefix}/{name}' if self.prefix else name
        try:
            if self.path.is_dir():
                return (self.path / rel).read_bytes()
            with zipfile.ZipFile(self.path) as archive:
                return archive.read(rel)
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            raise EvidenceError(f'Missing/unreadable source {rel} in {self.path}: {exc}') from exc


def load_b21(evidence: Source):
    raw = evidence.read(B21_NAME)
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EvidenceError('B21 evidence JSON is invalid') from exc
    if data.get('schema') != 'havenwild.elizawy_ground_composition_evidence.b21':
        raise EvidenceError('Unexpected B21 evidence schema')
    if any(data.get(k) is not False for k in ('visualApproval', 'productionApproval', 'runtimeCutover')):
        raise EvidenceError('Unexpected B21 approval flags; re-audit the input before generating B22')
    for upstream, name in [('upstreamB19Sha256', 'elizawy_master_ground_layout_b19.json'),
                           ('upstreamB20Sha256', 'elizawy_ground_source_regions_b20.json')]:
        if sha256(evidence.read(name)) != data[upstream]:
            raise EvidenceError(f'B21 upstream hash mismatch for {name}')
    return data, sha256(raw)


def crop_region(image, rect):
    x, y, w, h = rect
    return image.crop((x * TILE, y * TILE, (x + w) * TILE, (y + h) * TILE))


def uniform(tile) -> bool:
    return tile.getextrema() == tuple((v, v) for v in tile.getpixel((0, 0)))


def repeat(tile, w: int, h: int, Image):
    canvas = Image.new('RGBA', (w * TILE, h * TILE))
    for y in range(h):
        for x in range(w):
            canvas.paste(tile, (x * TILE, y * TILE))
    return canvas


def seal_test(image, tile, x, y):
    """Measure outer boundary pixel disagreements with the plain adjacent base.

    Diagnostic ONLY: nonzero does not prove a bad authored transition, and zero
    does not certify gameplay topology or arbitrary resizing.
    """
    sx, sy = x * TILE, y * TILE
    w, h = image.size
    base = tile.getpixel((0, 0))
    pixels = image.load()
    mismatch = 0
    for px in range(sx, sx + 3 * TILE):
        for py in (sy, sy + 3 * TILE - 1):
            mismatch += pixels[px, py] != base
    for py in range(sy, sy + 3 * TILE):
        for px in (sx, sx + 3 * TILE - 1):
            mismatch += pixels[px, py] != base
    return {'outerBoundarySamples': 4 * 3 * TILE, 'unequalToAdjacentPlainBase': mismatch}


def source_image(source: Source, name: str, Image):
    raw = source.read(name)
    try:
        im = Image.open(io.BytesIO(raw)).convert('RGBA')
        im.load()
    except Exception as exc:
        raise EvidenceError(f'Invalid original PNG {name}: {exc}') from exc
    if im.size != (512, 832):
        raise EvidenceError(f'Unexpected source sheet geometry for {name}: {im.size}')
    return raw, im


def paste_original(canvas, crop, x, y):
    canvas.alpha_composite(crop, dest=(x * TILE, y * TILE))


def verify_b21_previews(evidence: Source, season: str, source, surfaces, Image):
    checks = []
    for material, key in [('grass', 'grass'), ('sand', 'sand'), ('water', 'water')]:
        record = surfaces[f'ground.{material}.base' if material != 'water' else 'ground.water.base.visual']
        xy = record['sourceCell']
        src_cell = crop_region(source, (xy[0], xy[1], 1, 1))
        if not uniform(src_cell) or src_cell.getpixel((0, 0))[3] != 255:
            raise EvidenceError(f'{season} {material} base is not opaque and uniform')
        if not record['sourcePixelRepeatVerified'] or not record['sourceUniformColorVerified']:
            raise EvidenceError(f'{season} {material} B21 source base verification absent')
        png = f'b21_{season}_ground_{material}_base_repeat.png' if material != 'water' else f'b21_{season}_ground_water_base_visual_repeat.png'
        try:
            provided = Image.open(io.BytesIO(evidence.read(png))).convert('RGBA')
            provided.load()
        except Exception as exc:
            raise EvidenceError(f'Missing/invalid B21 repeat preview {png}: {exc}') from exc
        expected = repeat(src_cell, provided.width // TILE, provided.height // TILE, Image)
        if provided.size != expected.size or provided.tobytes() != expected.tobytes():
            raise EvidenceError(f'B21 repeat preview differs from original source: {png}')
        checks.append({'kind': 'base_repeat_pixels', 'id': material, 'preview': png, 'matched': True})
    for kind, original, name in [('grass_tuft', 'grass_tuft', 'grass_tuft_3x3'),
                                 ('grass_pool', 'grass_pool', 'pool_grass_bank_3x3')]:
        # Original 3x3 is source-exact. Never reuse the experimental 7x5 tile layout.
        filename = f'b21_{season}_ground_{name}_3x3_diagnostic.png'
        original_pixels = crop_region(source, REGIONS[original])
        try:
            submitted = Image.open(io.BytesIO(evidence.read(filename))).convert('RGBA')
            submitted.load()
        except Exception as exc:
            raise EvidenceError(f'Missing/invalid original B21 3x3: {filename}: {exc}') from exc
        if submitted.size != original_pixels.size or submitted.tobytes() != original_pixels.tobytes():
            raise EvidenceError(f'B21 3x3 differs from original source: {filename}')
        checks.append({'kind': 'original_3x3_pixels', 'id': kind, 'preview': filename, 'matched': True})
    return checks


def draw_contact_sheet(composites, out: Path, Image, ImageDraw):
    # Labels live OUTSIDE the source-art canvases. This is review UI, not game art.
    gap = 12
    margin = 18
    label_h = 25
    left_w, right_w = 24 * TILE, 12 * TILE
    row_h = 14 * TILE + label_h + gap
    image = Image.new('RGB', (left_w + right_w + 3 * margin, 5 * row_h + margin), (29, 32, 38))
    draw = ImageDraw.Draw(image)
    for index, (season, grass, sand) in enumerate(composites):
        y = margin + index * row_h
        draw.text((margin, y), f'{season.upper()} - AUTHORED 3x3 ONLY / GRASS DEMO (REVIEW)', fill=(242, 242, 242))
        draw.text((margin * 2 + left_w, y), 'SAND FEATURE - SQUARE SEAM / REJECTED', fill=(255, 217, 153))
        image.paste(grass.convert('RGB'), (margin, y + label_h))
        image.paste(sand.convert('RGB'), (margin * 2 + left_w, y + label_h))
    image.save(out)


def run(args) -> dict:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise EvidenceError('Pillow is needed only for the optional B22 review generator. Install it explicitly: python -m pip install Pillow') from exc
    evidence = Source(args.evidence, 'lpc' if args.evidence.is_file() else ('lpc' if (args.evidence / 'lpc').is_dir() else ''))
    terrain = Source(args.terrain, 'Terrain' if args.terrain.is_file() else ('Terrain' if (args.terrain / 'Terrain').is_dir() else ''))
    resolved_output = args.out.resolve()
    for guarded in (args.evidence, args.terrain):
        if guarded.is_dir() and (resolved_output == guarded.resolve() or guarded.resolve() in resolved_output.parents):
            raise EvidenceError(f'Output must not be inside original source/evidence directory: {args.out}')
    b21, b21_sha = load_b21(evidence)
    surfaces = {r['surfaceId']: r for r in b21['surfaces']}
    if set(surfaces) != {'ground.grass.base', 'ground.sand.base', 'ground.water.base.visual'}:
        raise EvidenceError('B21 base surface set changed; review before continuing')
    if any(not (r.get('previewOnly') and not r.get('gameplayApproved') and not r.get('runtimeApproved')) for r in surfaces.values()):
        raise EvidenceError('Unexpected source approval state')
    if b21.get('approvedResizes') != 0 or any(r.get('resizeApproved') is not False for r in b21['resizeExperiments']):
        raise EvidenceError('Unexpected B21 resize approval; re-audit input')
    report = {
        'schema': 'havenwild.elizawy_ground_landscape_evidence.b22',
        'status': 'GENERATED_SOURCE_EXACT_VISUAL_REVIEW_REQUIRED',
        'sourceProvider': 'elizawy_lpc_revised',
        'sourceCommit': b21['sourceCommit'],
        'b21Sha256': b21_sha,
        'compositionRules': ['plain original grass underlay', 'original 3x3 grass overlays',
                             'original unresized 3x3 banked ponds', 'isolated sand diagnostic only',
                             'no inferred grass-sand transition or resized pools'],
        'previewOnly': True,
        'automatedPixelVerification': False,
        'visualApproval': False,
        'topologyApproval': False,
        'gameplayApproval': False,
        'productionApproval': False,
        'runtimeCutover': False,
        'approvedExternalTransitions': 0,
        'approvedResizes': 0,
        'sourceHashes': {}, 'seasons': {},
        'rejectedCompositions': ['Raw sand_feature 3x3 pasted on the isolated plain sand tile: visible square boundary'],
        'blockers': ['Grass/sand junction lacks source-approved composition topology',
                     'Arbitrary-width water/pool/shoreline growth is not certified',
                     'Sandbox sand motif boundary needs manual visual inspection',
                     'Editor/client PIE parity and gameplay water semantics untested'],
    }
    # First verify every input fully; do not produce any output when upstream is corrupt.
    images = {}
    for season in SEASONS:
        source_name = f'terrain_{season}.png'
        original, image = source_image(terrain, source_name, Image)
        for surface in surfaces.values():
            bind = surface['seasonBindings'][season]
            if bind['sourcePath'] != f'Terrain/{source_name}' or sha256(original) != bind['sourceSha256']:
                raise EvidenceError(f'ElizaWy source SHA/path mismatch for {season}: {source_name}')
        checks = verify_b21_previews(evidence, season, image, surfaces, Image)
        images[season] = image
        report['sourceHashes'][source_name] = sha256(original)
        report['seasons'][season] = {'sourceVerified': True, 'b21PixelChecks': checks}
    report['automatedPixelVerification'] = True
    args.out.mkdir(parents=True, exist_ok=True)
    composites = []
    for season, source in images.items():
        grass_base = crop_region(source, (*surfaces['ground.grass.base']['sourceCell'], 1, 1))
        sand_base = crop_region(source, (*surfaces['ground.sand.base']['sourceCell'], 1, 1))
        grass = repeat(grass_base, 24, 14, Image)
        sand = repeat(sand_base, 12, 10, Image)
        layout = [('grass_tuft', 2, 2), ('grass_pool', 9, 3),
                  ('grass_tuft', 18, 8), ('grass_pool', 4, 9)]
        diagnostics = []
        for item, x, y in layout:
            exact = crop_region(source, REGIONS[item])
            paste_original(grass, exact, x, y)
            diagnostics.append({'sourceRegion': item, 'tilePosition': [x, y],
                                'unmodifiedSourcePixels': True,
                                'boundaryDiagnostic': seal_test(grass, grass_base, x, y)})
        sand_feature = crop_region(source, REGIONS['sand_feature'])
        paste_original(sand, sand_feature, 4, 3)
        grass_filename = f'b22_{season}_grass_pond_authored_only.png'
        sand_filename = f'b22_{season}_sand_isolated_UNAPPROVED.png'
        grass.save(args.out / grass_filename)
        sand.save(args.out / sand_filename)
        # Verify interior pixels against source where alpha is fully opaque.
        for key, x, y in layout:
            exact = crop_region(source, REGIONS[key])
            placed = grass.crop((x * TILE, y * TILE, (x + 3) * TILE, (y + 3) * TILE))
            original_pixels = exact.load()
            placed_pixels = placed.load()
            for py in range(3 * TILE):
                for px in range(3 * TILE):
                    if original_pixels[px, py][3] == 255 and placed_pixels[px, py] != original_pixels[px, py]:
                        raise EvidenceError(f'Original overlay pixels mutated: {season} {key}')
        sand_boundary = seal_test(sand, sand_base, 4, 3)
        report['seasons'][season]['composition'] = {
            'grassPreview': grass_filename, 'sandPreview': sand_filename,
            'grassSceneTileSize': [24, 14], 'sandDiagnosticTileSize': [12, 10],
            'sourceRegionsPlaced': diagnostics,
            'sandFeatureBoundaryDiagnostic': sand_boundary,
            'sandFeatureStandaloneRejected': sand_boundary['unequalToAdjacentPlainBase'] > 0,
            'interpretation': 'review-only visual examples; no material/topology promotion',
        }
        composites.append((season, grass, sand))
    draw_contact_sheet(composites, args.out / 'B22_all_seasons_review.png', Image, ImageDraw)
    report['previewCount'] = 11
    report['previews'] = [f'b22_{s}_{t}' for s in SEASONS for t in
                          ('grass_pond_authored_only.png', 'sand_isolated_UNAPPROVED.png')] + ['B22_all_seasons_review.png']
    (args.out / 'elizawy_ground_landscape_b22.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True, help='lpc(5).zip or directory containing lpc/ B21 evidence')
    parser.add_argument('--terrain', type=Path, required=True, help='original Terrain.zip or folder containing Terrain PNGs')
    parser.add_argument('--out', type=Path, required=True, help='generated evidence folder, not original source tree')
    args = parser.parse_args()
    try:
        report = run(args)
    except (EvidenceError, OSError, KeyError, ValueError) as exc:
        print(f'B22 FAIL: {exc}', file=sys.stderr)
        return 1
    print('B22 PASS: source SHA + B21 original pixel verification across five seasons.')
    print(f'B22 PREVIEW ONLY: {report["previewCount"]} images, zero production/resize/gameplay approvals.')
    print(f'Evidence: {args.out / "elizawy_ground_landscape_b22.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
