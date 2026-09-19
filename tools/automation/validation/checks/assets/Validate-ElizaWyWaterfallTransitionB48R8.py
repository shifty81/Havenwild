#!/usr/bin/env python3
"""Source-exact validation; not proof of joins, rendering, collision or runtime cutover."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
import zipfile

MAP_PATH = 'content/assets/lpc/elizawy_mountain_waterfall_transition_source_b48r8_v0_1.json'
EXPECTED_SHEET = 'assets/source/licensed/lpc_revised/Terrain/Mountain, Waterfall Transitions (Summer).png'
EXPECTED_ARCHIVE_MEMBER = 'Terrain/Mountain, Waterfall Transitions (Summer).png'
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def decode_rgba_png(raw):
    """Decode 8-bit noninterlaced RGBA PNG with native scanline filters; no Pillow dependency."""
    if not raw.startswith(PNG_MAGIC):
        raise ValueError('not a PNG')
    pos = len(PNG_MAGIC)
    chunks = []
    width = height = None
    ended = False
    while pos + 12 <= len(raw):
        size = struct.unpack_from('>I', raw, pos)[0]
        kind = raw[pos+4:pos+8]
        end = pos+12+size
        if end > len(raw):
            raise ValueError('truncated PNG chunk')
        data = raw[pos+8:pos+8+size]
        checksum = struct.unpack_from('>I', raw, pos+8+size)[0]
        if (zlib.crc32(kind+data)&0xffffffff) != checksum:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            if size != 13 or width is not None:
                raise ValueError('invalid IHDR')
            width,height,depth,mode,comp,filt,interlace=struct.unpack('>IIBBBBB',data)
            if (depth,mode,comp,filt,interlace)!=(8,6,0,0,0):
                raise ValueError('expected original RGBA8 PNG')
            if width < 1 or height < 1 or width > 4096 or height > 4096:
                raise ValueError('invalid dimensions')
        if kind == b'IDAT':
            chunks.append(data)
        if kind == b'IEND':
            ended = True
            if end != len(raw):
                raise ValueError('unexpected bytes after IEND')
            break
        pos=end
    if not ended or width is None or not chunks:
        raise ValueError('incomplete PNG')
    stride=width*4
    expanded=zlib.decompress(b''.join(chunks))
    if len(expanded)!=height*(stride+1):
        raise ValueError('wrong PNG decoded size')
    pixels=bytearray(width*height*4)
    prior=bytearray(stride)
    for y in range(height):
        off=y*(stride+1)
        f=expanded[off]
        row=bytearray(expanded[off+1:off+1+stride])
        if f>4:
            raise ValueError('invalid PNG filter')
        for i in range(stride):
            left=row[i-4] if i>=4 else 0
            up=prior[i]
            upper_left=prior[i-4] if i>=4 else 0
            if f==1:pred=left
            elif f==2:pred=up
            elif f==3:pred=(left+up)//2
            elif f==4:
                p=left+up-upper_left
                a,b,c=abs(p-left),abs(p-up),abs(p-upper_left)
                pred=left if a<=b and a<=c else (up if b<=c else upper_left)
            else:pred=0
            row[i]=(row[i]+pred)&255
        pixels[y*stride:(y+1)*stride]=row
        prior=row
    return width,height,bytes(pixels)


def tile_bytes(image,width,x,y):
    return b''.join(image[((y*32+row)*width+x*32)*4:((y*32+row)*width+(x+1)*32)*4]
                    for row in range(32))


def validate(repo, reference_zip=None):
    mapping=json.loads((repo/MAP_PATH).read_text(encoding='utf-8'))
    src=mapping['authority']
    if mapping['schema']!='havenwild.elizawy.mountain_waterfall_transition_source.v0_1' or mapping['productionEnabled'] is not False:
        raise ValueError('schema or production-activation mismatch')
    if src['installedSourcePath']!=EXPECTED_SHEET or src['archiveMember']!=EXPECTED_ARCHIVE_MEMBER:
        raise ValueError('source identity mismatch')
    blob=(repo/src['gitRetainedOriginalPngBlob']).read_bytes()
    raw=(repo/EXPECTED_SHEET).read_bytes()
    if raw != blob:
        raise ValueError('mounted PNG differs from Git-retained original blob')
    if sha256(raw)!=src['sourceSha256']:
        raise ValueError('source PNG SHA mismatch')
    width,height,image=decode_rgba_png(raw)
    if (width,height)!=(192,224) or src['sourceImageSizePx']!=[192,224]:
        raise ValueError('source dimension mismatch')
    cells=mapping['cells']
    if len(cells)!=42 or {tuple(c['grid']) for c in cells}!={(x,y) for x in range(6) for y in range(7)}:
        raise ValueError('source cell inventory incomplete or duplicated')
    expected={'exactCells':42,'matchingCanonicalCliffAtlas':10,'notInCanonicalCliffAtlas':32,'missingFromEntireOriginalTerrainZip':32}
    if mapping['counts']!=expected:
        raise ValueError('source totals mismatch')
    matching=0
    for cell in cells:
        x,y=cell['grid']
        if cell['sourceRectPx']!=[x*32,y*32,32,32] or cell['runtimeEligible'] is not False:
            raise ValueError('incorrect source cell address or unsafe promotion')
        if sha256(tile_bytes(image,width,x,y))!=cell['pixelSha256']:
            raise ValueError('source cell pixel mismatch %s'%cell['grid'])
        matching+=bool(cell['exactMatchInCliffSummer'])
    if matching!=10:
        raise ValueError('legacy cliff atlas exact-match count changed')
    credits=(repo/'assets/source/licensed/lpc_revised/Terrain/REFERENCE_PACK_TERRAIN_CREDITS.txt').read_bytes()
    if credits!=(repo/src['gitRetainedOriginalCredits']).read_bytes():
        raise ValueError('mounted credits differ from Git-retained credits')
    for phrase in [b'Mountain (Base, Animated Water, Features, Vines, Waterfall Transitions)',b'Eliza Wyatt',b'OGA-BY 3.0']:
        if phrase not in credits:
            raise ValueError('original artist credits/attribution missing')
    if reference_zip is not None:
        with zipfile.ZipFile(reference_zip) as original:
            if original.read(EXPECTED_ARCHIVE_MEMBER)!=raw or original.read('Terrain/Credits.txt')!=credits:
                raise ValueError('reference-pack source bytes differ')
    print('PASS B48R8: 42/42 source pixel hashes, 32 recovered missing cells, credentials/provenance intact, runtime promotion blocked')
    return mapping


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[5])
    p.add_argument('--reference-zip',type=Path)
    args=p.parse_args()
    try:
        validate(args.repo,args.reference_zip)
        return 0
    except (ValueError,KeyError,FileNotFoundError,zipfile.BadZipFile,zlib.error) as exc:
        print('FAIL B48R8:',exc)
        return 1

if __name__=='__main__':sys.exit(main())
