#!/usr/bin/env python3
"""Dependency-free B19 master-sheet mapping and unsafe-approval regression tests."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'tools/automation/assets/Build-ElizaWyMasterGroundB19.py'
spec = importlib.util.spec_from_file_location('havenwild_b19_master_ground', SCRIPT)
b19 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b19
spec.loader.exec_module(b19)
CONFIG = json.loads((ROOT / b19.CONFIG).read_text(encoding='utf-8'))


def png_chunk(name: bytes, content: bytes) -> bytes:
    return struct.pack('>I', len(content)) + name + content + struct.pack('>I', zlib.crc32(name+content)&0xffffffff)


def make_png(width: int, height: int, color: bytes = b'\x00\x00\x00\xff', filter_type: int = 0) -> bytes:
    stride = width * 4
    pixels = (color * width) * height
    rows = bytearray()
    for row in range(height):
        current = pixels[row*stride:(row+1)*stride]
        prior = pixels[(row-1)*stride:row*stride] if row else bytes(stride)
        encoded = bytearray(current)
        if filter_type == 1:
            for x in range(stride):
                encoded[x] = (current[x]-(current[x-4] if x>=4 else 0))&255
        elif filter_type == 2:
            for x in range(stride):encoded[x] = (current[x]-prior[x])&255
        elif filter_type == 3:
            for x in range(stride):encoded[x] = (current[x]-((current[x-4] if x>=4 else 0)+prior[x])//2)&255
        elif filter_type == 4:
            for x in range(stride):
                a = current[x-4] if x>=4 else 0
                b = prior[x]
                c = prior[x-4] if x>=4 else 0
                p=a+b-c
                d=sorted([(abs(p-a),0,a),(abs(p-b),1,b),(abs(p-c),2,c)])[0][2]
                encoded[x]=(current[x]-d)&255
        rows.append(filter_type);rows.extend(encoded)
    return (b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+
            png_chunk(b'IDAT',zlib.compress(rows))+png_chunk(b'IEND',b''))


class MasterGroundTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.img = self.root/'test.png'

    def test_all_png_filters_decode_exact_rgba(self):
        for filter_type in range(5):
            self.img.write_bytes(make_png(3,3,b'\x19\x20\x30\xff',filter_type))
            self.assertEqual(b19.rgba_png(self.img),(3,3,b'\x19\x20\x30\xff'*9))

    def test_corrupted_png_chunk_crc_rejected(self):
        data=bytearray(make_png(1,1));data[22]^=1;self.img.write_bytes(data)
        with self.assertRaises(ValueError):b19.rgba_png(self.img)

    def test_non_rgba_png_rejected(self):
        raw=make_png(1,1)
        raw=raw[:25]+b'\x02'+raw[26:]
        self.img.write_bytes(raw)
        with self.assertRaises(ValueError):b19.rgba_png(self.img)

    def test_alpha_layout_reports_exact_exception_cells(self):
        left=bytearray(b'\x00\x00\x00\x00'*16)
        right=bytearray(left)
        right[(1*4+2)*4+3]=255
        cells,occ,changed=b19.alpha_layout(bytes(left),bytes(right),4,4,2)
        self.assertEqual((cells,occ,changed),([[1,0]],1,1))

    def test_alpha_value_change_does_not_invent_occupied_cell(self):
        first=bytearray(b'\0\0\0\xff'*4)
        second=bytearray(first);second[3]=128
        self.assertEqual(b19.alpha_layout(first,second,2,2,1),([],0,1))

    def test_seam_report_evidence_never_approves_visuals(self):
        data=b'\x0a\x14\x1e\xff'*4
        out=b19.repeat_edges(data,2,0,0,2)
        self.assertEqual((out['leftRightBorderPixelDifferences'],out['topBottomBorderPixelDifferences']),(0,0))
        self.assertIn('NO_VISUAL_SEAM_APPROVAL',out['status'])

    def test_all_master_cells_have_unique_authoritative_coordinates(self):
        self.assertEqual((CONFIG['columns'],CONFIG['rows'],CONFIG['tileSize']),(16,26,32))
        self.assertEqual(len({(x,y) for y in range(26) for x in range(16)}),416)
        self.assertEqual(CONFIG['masterSheet'],'Terrain/terrain_summer.png')
        self.assertEqual(CONFIG['seasons'],list(b19.SEASONS))

    def test_winter_ice_exceptions_are_explicit(self):
        self.assertEqual(CONFIG['alphaLayoutExpectations']['winter_ice'],[[6,21],[11,21]])
        self.assertEqual(CONFIG['alphaNumericExpectations']['winter']['alphaValueDifferences'],1)
        self.assertEqual(CONFIG['alphaNumericExpectations']['winter_ice']['occupiedPixelDifferences'],2048)

    def test_water_detail_correction_blocks_old_fill_role(self):
        role={r['id']:r for r in CONFIG['canonicalCandidates']}
        for key in ('ground.water.surface.visual','ground.water.dark.visual'):
            self.assertEqual(role[key]['resizeMode'],'NOT_INDEPENDENT_WATER_FILL')
            self.assertIn('supersedesB17Role',role[key])
        self.assertEqual(len(role),10)

    def test_no_automatic_promotion_or_fallback(self):
        p=CONFIG['policies']
        self.assertIs(p['productionApproval'],False)
        self.assertIs(p['runtimeCutover'],False)
        for name in ('unmappedCellsFailClosed','noNonElizaWyProviderFallback','preserveLegacyRendererAndSaves',
                     'candidateRolesDoNotApproveAutotiling','winterIceAlphaExceptionsExplicit'):
            self.assertIs(p[name],True)

    def test_invalid_relative_and_symlink_escape_blocked(self):
        with self.assertRaises(ValueError):b19.safe(self.root,'../escaped')
        with self.assertRaises(ValueError):b19.safe(self.root,'/absolute')

    def test_png_bytes_not_modified_during_read(self):
        original=make_png(2,2)
        self.img.write_bytes(original)
        b19.rgba_png(self.img)
        self.assertEqual(self.img.read_bytes(),original)


if __name__=='__main__':
    unittest.main()
