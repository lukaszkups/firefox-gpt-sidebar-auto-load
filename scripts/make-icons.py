#!/usr/bin/env python3
"""Draw the toolbar icon as a PNG without third-party libraries."""

import struct
import zlib
from pathlib import Path


def chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def circle_coverage(px, py, cx, cy, radius):
    distance = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
    return max(0.0, min(1.0, radius + 0.5 - distance))


def round_rect_coverage(px, py, left, top, right, bottom, radius):
    nearest_x = min(max(px, left + radius), right - radius)
    nearest_y = min(max(py, top + radius), bottom - radius)
    distance = ((px - nearest_x) ** 2 + (py - nearest_y) ** 2) ** 0.5
    return max(0.0, min(1.0, radius + 0.5 - distance))


def blend(dst, src, alpha):
    out = [0, 0, 0, 0]
    src_a = src[3] * alpha / 255
    dst_a = dst[3] / 255
    out_a = src_a + dst_a * (1 - src_a)
    if out_a <= 0:
        return (0, 0, 0, 0)
    for i in range(3):
        out[i] = round((src[i] * src_a + dst[i] * dst_a * (1 - src_a)) / out_a)
    out[3] = round(out_a * 255)
    return tuple(out)


def pixel(x, y, size):
    px = x + 0.5
    py = y + 0.5
    blue = (0, 96, 223, 255)
    white = (255, 255, 255, 255)
    color = (0, 0, 0, 0)
    margin = size * 0.04
    color = blend(
        color,
        blue,
        circle_coverage(px, py, size / 2, size / 2, size / 2 - margin),
    )
    # Antenna
    color = blend(color, white, circle_coverage(px, py, size * 0.50, size * 0.18, size * 0.05))
    color = blend(
        color,
        white,
        round_rect_coverage(
            px, py, size * 0.47, size * 0.20, size * 0.53, size * 0.34, size * 0.02
        ),
    )
    # Head
    color = blend(
        color,
        white,
        round_rect_coverage(px, py, size * 0.22, size * 0.32, size * 0.78, size * 0.82, size * 0.14),
    )
    # Eyes and mouth, punched in the same blue as the background
    color = blend(color, blue, circle_coverage(px, py, size * 0.37, size * 0.50, size * 0.07))
    color = blend(color, blue, circle_coverage(px, py, size * 0.63, size * 0.50, size * 0.07))
    color = blend(
        color,
        blue,
        round_rect_coverage(px, py, size * 0.36, size * 0.66, size * 0.64, size * 0.72, size * 0.03),
    )
    return color


def write_png(path, size):
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            raw.extend(pixel(x, y, size))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    root = Path(__file__).resolve().parents[1] / "icons"
    root.mkdir(parents=True, exist_ok=True)
    for size in (32, 48, 96):
        write_png(root / f"robot-{size}.png", size)


if __name__ == "__main__":
    main()
