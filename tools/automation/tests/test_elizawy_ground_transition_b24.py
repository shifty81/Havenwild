"""Stdlib-only B24 algorithm tests (no Pillow or source ZIP needed for normal gate)."""
from __future__ import annotations
import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = (Path(__file__).resolve().parents[1] / 'assets' /
          'Build-ElizaWyGroundTransitionEvidenceB24.py')
spec = importlib.util.spec_from_file_location('havenwild_b24', MODULE)
b24 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(b24)


class FakeImage:
    def __init__(self, width=96, height=96, color=(244, 215, 160, 255)):
        self.size = (width, height)
        self.pixels = [[color] * width for _ in range(height)]

    def getpixel(self, point):
        x, y = point
        return self.pixels[y][x]

    def putpixel(self, point, color):
        x, y = point
        self.pixels[y][x] = color


class BoundaryTests(unittest.TestCase):
    def test_constant_exact_boundary_is_384_samples(self):
        im = FakeImage()
        result = b24.signature(im)
        self.assertEqual(result['samples'], 384)
        self.assertEqual(result['opaque'], 384)
        self.assertEqual(result['colors'][0]['count'], 384)

    def test_source_highlights_preserved_and_positioned(self):
        pale = (244,215,160,255)
        highlight = (238,204,140,255)
        im = FakeImage(color=pale)
        pts = ([(x,0) for x in range(40,44)] + [(x,0) for x in range(52,56)]
               + [(95,y) for y in range(40,44)] + [(95,y) for y in range(52,56)])
        for point in pts:
            im.putpixel(point, highlight)
        found = b24.warm_exceptions(im, pale)
        self.assertEqual(len(found), 16)
        self.assertEqual({tuple(v['pixel']) for v in found}, set(pts))
        self.assertEqual({tuple(v['rgba']) for v in found}, {highlight})

    def test_transparency_not_misclassified_as_pale(self):
        im = FakeImage()
        im.putpixel((50, 0), (0,0,0,0))
        report = b24.signature(im)
        self.assertEqual(report['opaque'], 383)
        self.assertEqual(len(b24.warm_exceptions(im, (244,215,160,255))), 1)

    def test_no_out_of_boundary_points(self):
        im = FakeImage()
        im.putpixel((5, 5), (0,0,0,0))
        self.assertEqual(len(b24.warm_exceptions(im,(244,215,160,255))),0)


if __name__ == '__main__':
    unittest.main()
