#!/usr/bin/env python3
"""Render this repo's small solid SVG vocabulary into a macOS iconset."""

import math
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib


SVG = "{http://www.w3.org/2000/svg}"
SAMPLES = 4


def rgb(value):
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value or ""):
        raise ValueError("Colors must be opaque RGB hex values.")
    return bytes(int(value[index:index + 2], 16) for index in (1, 3, 5))


def shapes(path):
    root = ET.parse(path).getroot()
    if root.tag != SVG + "svg" or root.attrib != {"width": "1024", "height": "1024", "viewBox": "0 0 1024 1024"}:
        raise ValueError("The master must use a 1024-square viewBox.")
    result = []
    for node in root:
        if node.tag in (SVG + "title", SVG + "desc"):
            continue
        numbers = lambda keys: tuple(float(node.get(key, "0")) for key in keys)
        if node.tag == SVG + "rect" and not set(node.attrib) - {"x", "y", "width", "height", "rx", "fill"}:
            x, y, width, height, radius = numbers(("x", "y", "width", "height", "rx"))
            if width <= 0 or height <= 0 or not 0 <= radius <= min(width, height) / 2:
                raise ValueError("Invalid rectangle geometry.")
            bounds = x, y, x + width, y + height
            def inside(px, py, x=x, y=y, width=width, height=height, radius=radius):
                dx = max(x + radius - px, 0, px - (x + width - radius))
                dy = max(y + radius - py, 0, py - (y + height - radius))
                return x <= px <= x + width and y <= py <= y + height and dx * dx + dy * dy <= radius * radius
            color, convex = rgb(node.get("fill")), True
        elif node.tag == SVG + "circle" and not set(node.attrib) - {"cx", "cy", "r", "fill", "stroke", "stroke-width"}:
            cx, cy, radius, stroke = numbers(("cx", "cy", "r", "stroke-width"))
            if node.get("fill") != "none" or radius <= 0 or not 0 < stroke <= 2 * radius:
                raise ValueError("Only an outlined circular lens is supported.")
            outer, inner = radius + stroke / 2, radius - stroke / 2
            bounds = cx - outer, cy - outer, cx + outer, cy + outer
            def inside(px, py, cx=cx, cy=cy, inner=inner, outer=outer):
                return inner * inner <= (px - cx) ** 2 + (py - cy) ** 2 <= outer * outer
            color, convex = rgb(node.get("stroke")), False
        elif node.tag == SVG + "line" and not set(node.attrib) - {"x1", "y1", "x2", "y2", "stroke", "stroke-width", "stroke-linecap"}:
            x1, y1, x2, y2, stroke = numbers(("x1", "y1", "x2", "y2", "stroke-width"))
            if stroke <= 0 or node.get("stroke-linecap") != "round":
                raise ValueError("Only round-capped lines are supported.")
            radius, dx, dy = stroke / 2, x2 - x1, y2 - y1
            length = dx * dx + dy * dy
            if not length:
                raise ValueError("The handle needs distinct endpoints.")
            bounds = min(x1, x2) - radius, min(y1, y2) - radius, max(x1, x2) + radius, max(y1, y2) + radius
            def inside(px, py, x1=x1, y1=y1, dx=dx, dy=dy, length=length, radius=radius):
                along = min(1, max(0, ((px - x1) * dx + (py - y1) * dy) / length))
                return (px - x1 - along * dx) ** 2 + (py - y1 - along * dy) ** 2 <= radius * radius
            color, convex = rgb(node.get("stroke")), True
        else:
            raise ValueError("Unsupported SVG element or attribute.")
        if len(node) or not all(math.isfinite(value) for value in bounds) or not (0 <= bounds[0] < bounds[2] <= 1024 and 0 <= bounds[1] < bounds[3] <= 1024):
            raise ValueError("Artwork must remain finite and within its square canvas.")
        result.append((bounds, inside, color, convex))
    if not 1 <= len(result) <= 32:
        raise ValueError("Artwork must contain one to 32 simple shapes.")
    return result


def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def render(art, size):
    pixels = bytearray(size * size * 4)
    scale = 1024 / size
    samples = SAMPLES * SAMPLES
    for (left, top, right, bottom), inside, color, convex in art:
        for row in range(max(0, math.floor(top / scale)), min(size, math.ceil(bottom / scale))):
            for column in range(max(0, math.floor(left / scale)), min(size, math.ceil(right / scale))):
                full = convex and all(inside(x * scale, y * scale) for x, y in ((column, row), (column + 1, row), (column, row + 1), (column + 1, row + 1)))
                coverage = samples if full else sum(inside((column + (sx + 0.5) / SAMPLES) * scale, (row + (sy + 0.5) / SAMPLES) * scale) for sy in range(SAMPLES) for sx in range(SAMPLES))
                if not coverage:
                    continue
                index = (row * size + column) * 4
                alpha = (coverage * 255 + samples // 2) // samples
                previous = pixels[index + 3]
                combined = alpha + (previous * (255 - alpha) + 127) // 255
                for channel in range(3):
                    premultiplied = color[channel] * alpha + (pixels[index + channel] * previous * (255 - alpha) + 127) // 255
                    pixels[index + channel] = min(255, (premultiplied + combined // 2) // combined)
                pixels[index + 3] = combined
    scanlines = b"".join(b"\0" + pixels[row * size * 4:(row + 1) * size * 4] for row in range(size))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"sRGB", b"\0") + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b"")


def package_iconset(directory, output):
    # Each chunk length and the family length include their eight-byte header.
    slots = (
        (b"icp4", "icon_16x16.png"), (b"ic11", "icon_16x16@2x.png"),
        (b"icp5", "icon_32x32.png"), (b"ic12", "icon_32x32@2x.png"),
        (b"ic07", "icon_128x128.png"), (b"ic13", "icon_128x128@2x.png"),
        (b"ic08", "icon_256x256.png"), (b"ic14", "icon_256x256@2x.png"),
        (b"ic09", "icon_512x512.png"), (b"ic10", "icon_512x512@2x.png"),
    )
    parts = []
    for kind, name in slots:
        png = (directory / name).read_bytes()
        parts.append(kind + struct.pack(">I", len(png) + 8) + png)
    body = b"".join(parts)
    output.write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: render_app_icon.py master.svg output.iconset output.icns")
    artwork = shapes(Path(sys.argv[1]))
    destination = Path(sys.argv[2])
    icon = Path(sys.argv[3])
    if destination.suffix != ".iconset" or destination.exists():
        raise SystemExit("The output must be a new iconset directory.")
    if icon.suffix != ".icns" or icon.exists() or icon.is_symlink() or icon.parent != destination.parent:
        raise SystemExit("The ICNS output must be a new sibling file of the iconset.")
    destination.mkdir()
    images = {}
    for points in (16, 32, 128, 256, 512):
        for density in (1, 2):
            size = points * density
            if size not in images:
                images[size] = render(artwork, size)
            suffix = "@2x" if density == 2 else ""
            (destination / f"icon_{points}x{points}{suffix}.png").write_bytes(images[size])
    package_iconset(destination, icon)
