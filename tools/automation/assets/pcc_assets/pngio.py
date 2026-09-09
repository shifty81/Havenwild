from __future__ import annotations

import binascii
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Image:
    width: int
    height: int
    rgba: bytes

    def pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        i = (y * self.width + x) * 4
        d = self.rgba
        return d[i], d[i + 1], d[i + 2], d[i + 3]


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
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += length + 12
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif kind == b"PLTE":
            palette = [tuple(payload[i:i+3]) for i in range(0, len(payload), 3)]
        elif kind == b"tRNS":
            transparency = bytes(payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break

    if ihdr is None:
        raise ValueError(f"PNG missing IHDR: {path}")

    width, height, bit_depth, color_type, compression, filter_method, interlace = ihdr
    if bit_depth != 8:
        raise ValueError(f"unsupported PNG bit depth {bit_depth}: {path}")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ValueError(f"unsupported PNG encoding mode: {path}")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"unsupported PNG color type {color_type}: {path}")
    if color_type == 3 and palette is None:
        raise ValueError(f"indexed PNG missing palette: {path}")

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    if len(raw) != height * (stride + 1):
        raise ValueError(f"unexpected PNG payload size: {path}")

    scan = bytearray(height * stride)
    src = 0
    for y in range(height):
        f = raw[src]
        src += 1
        row = bytearray(raw[src:src + stride])
        src += stride
        prev = (y - 1) * stride
        cur = y * stride
        for x in range(stride):
            a = row[x - channels] if x >= channels else 0
            b = scan[prev + x] if y > 0 else 0
            c = scan[prev + x - channels] if y > 0 and x >= channels else 0
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
            scan[cur + x] = value

    rgba = bytearray(width * height * 4)
    for y in range(height):
        row = scan[y * stride:(y + 1) * stride]
        for x in range(width):
            si = x * channels
            di = (y * width + x) * 4
            if color_type == 6:
                rgba[di:di+4] = row[si:si+4]
            elif color_type == 2:
                rgba[di:di+3] = row[si:si+3]
                rgba[di+3] = 255
            elif color_type == 3:
                idx = row[si]
                r, g, b = palette[idx]
                a = transparency[idx] if transparency is not None and idx < len(transparency) else 255
                rgba[di:di+4] = bytes((r, g, b, a))
            elif color_type == 0:
                g = row[si]
                rgba[di:di+4] = bytes((g, g, g, 255))
            elif color_type == 4:
                g, a = row[si], row[si+1]
                rgba[di:di+4] = bytes((g, g, g, a))

    return Image(width, height, bytes(rgba))


def encode_png(path: Path, image: Image) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
        )

    raw = bytearray()
    stride = image.width * 4
    for y in range(image.height):
        raw.append(0)
        start = y * stride
        raw.extend(image.rgba[start:start+stride])

    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)))
    out.extend(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    out.extend(chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
