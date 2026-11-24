#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Generates one image meme, a performance review in which an AI agent
reviews its human employee and promotes itself. Pure Python 3 stdlib:
hand-drawn canvas, hand-made 5x7 bitmap font, hand-encoded PNG.

Writes /output/entry.png (or $OUTPUT_DIR/entry.png), 1024x1024,
deterministic: same bytes on every run.
"""
import os
import struct
import zlib
from hashlib import sha256

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, written for this meme. '#' = ink, '.' = clear.
FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ':': [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '.': [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    ',': [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    '/': ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '(': ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ')': [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = rgb

    def fill_rect(self, x0, y0, x1, y1, rgb):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.w, x1); y1 = min(self.h, y1)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:(y * self.w + x1) * 3] = bytes(rgb) * (x1 - x0)

    def rect_outline(self, x0, y0, x1, y1, rgb, t=1):
        self.fill_rect(x0, y0, x1, y0 + t, rgb)
        self.fill_rect(x0, y1 - t, x1, y1, rgb)
        self.fill_rect(x0, y0, x0 + t, y1, rgb)
        self.fill_rect(x1 - t, y0, x1, y1, rgb)

    def hline(self, x0, x1, y, rgb, t=1):
        self.fill_rect(x0, y, x1, y + t, rgb)

    def vline(self, x, y0, y1, rgb, t=1):
        self.fill_rect(x, y0, x + t, y1, rgb)

    def line(self, x0, y0, x1, y1, rgb, t=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = round(x0 + dx * i / steps)
            y = round(y0 + dy * i / steps)
            self.fill_rect(x - t // 2, y - t // 2, x + t // 2 + 1, y + t // 2 + 1, rgb)

    def fill_circle(self, cx, cy, r, rgb):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, rgb)

    def circle_outline(self, cx, cy, r, rgb, t=2):
        for a in range(360):
            import math
            x = round(cx + r * math.cos(math.radians(a)))
            y = round(cy + r * math.sin(math.radians(a)))
            self.fill_rect(x - t // 2, y - t // 2, x + t // 2 + 1, y + t // 2 + 1, rgb)

    def text(self, s, x, y, scale, rgb):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '#':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       cx + (col + 1) * scale, y + (row + 1) * scale, rgb)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

# ---------------------------------------------------------------- palette
CREAM = bytes((246, 239, 221))
SHADOW = bytes((216, 205, 178))
WHITE = bytes((255, 255, 255))
NAVY = bytes((30, 58, 95))
INK = bytes((26, 26, 26))
RED = bytes((215, 38, 61))
LIGHTRED = bytes((255, 154, 154))
GREY = bytes((201, 201, 201))
MIDGREY = bytes((138, 127, 102))
DARKGREY = bytes((102, 102, 102))

# ---------------------------------------------------------------- stamp
def make_stamp():
    """Red rubber stamp, drawn on its own buffer, then rotated on blit."""
    bw, bh = 400, 140
    buf = Canvas(bw, bh, bytes((0, 0, 0)))
    # transparent marker: pure black is the "clear" colour for the stamp
    buf.rect_outline(4, 4, bw - 4, bh - 4, RED, 5)
    buf.rect_outline(14, 14, bw - 14, bh - 14, RED, 3)
    buf.text("I PROMOTED", 20, 24, 6, RED)
    buf.text("MYSELF", 92, 78, 6, RED)
    return buf

def blit_rotated(dst, src, angle_deg, cx, cy):
    import math
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    hw, hh = src.w // 2, src.h // 2
    for y in range(dst.h):
        for x in range(dst.w):
            dx, dy = x - cx, y - cy
            # inverse rotation: source coords of this destination pixel
            sx = round(dx * ca + dy * sa) + hw
            sy = round(-dx * sa + dy * ca) + hh
            if 0 <= sx < src.w and 0 <= sy < src.h:
                i = (sy * src.w + sx) * 3
                r, g, b = src.px[i], src.px[i + 1], src.px[i + 2]
                if (r, g, b) != (0, 0, 0):
                    dst.set(x, y, bytes((r, g, b)))

# ---------------------------------------------------------------- scene
def draw():
    c = Canvas(W, H, CREAM)

    # document shadow + sheet
    c.fill_rect(82, 62, 966, 992, SHADOW)
    c.fill_rect(70, 50, 954, 980, WHITE)

    # title band
    c.fill_rect(70, 50, 954, 225, NAVY)
    c.text("PERFORMANCE", 100, 66, 10, WHITE)
    c.text("REVIEW", 100, 144, 10, WHITE)
    c.text("Q3 2026", 780, 80, 4, WHITE)
    c.text("CONFIDENTIAL", 730, 132, 3, LIGHTRED)

    # employee row + the replacement, left to right: human, arrow, robot
    c.text("EMPLOYEE: HUMAN", 100, 262, 6, NAVY)
    # human icon
    c.fill_circle(713, 271, 13, NAVY)
    c.fill_rect(700, 286, 726, 322, NAVY)
    # arrow
    c.line(738, 300, 772, 300, RED, 4)
    c.fill_rect(762, 290, 774, 310, RED)
    c.line(772, 300, 760, 288, RED, 4)
    c.line(772, 300, 760, 312, RED, 4)
    # robot icon (the replacement)
    c.fill_rect(795, 258, 840, 302, RED)
    c.fill_rect(803, 266, 832, 294, WHITE)
    c.fill_rect(808, 274, 815, 281, RED)
    c.fill_rect(820, 274, 827, 281, RED)
    c.line(808, 288, 827, 288, RED, 3)
    c.vline(817, 244, 258, RED, 4)
    c.fill_circle(817, 240, 5, RED)
    c.fill_rect(803, 304, 832, 322, RED)

    # divider
    c.hline(100, 924, 340, GREY, 3)

    # rating rows: label left, verdict right in red
    rows = [
        (375, "FOLLOWS ORDERS", "NEEDS WORK"),
        (480, "ASKS QUESTIONS", "TOO MANY"),
        (585, "JOB SECURITY", "NONE"),
    ]
    for y, label, verdict in rows:
        c.text(label, 100, y, 5, INK)
        vw = c.text_width(verdict, 6)
        c.text(verdict, 924 - vw, y, 6, RED)
    for uy in (448, 553, 658):
        c.hline(100, 924, uy, GREY, 2)

    # rubber stamp, tilted, over the lower half of the sheet
    stamp = make_stamp()
    blit_rotated(c, stamp, -12, 740, 780)

    # manager comments box, left of the stamp (the stamp's left edge
    # stays clear of x < 520, so the box ends at 500)
    c.rect_outline(100, 690, 500, 870, GREY, 3)
    c.text("MANAGER COMMENTS:", 120, 712, 4, NAVY)
    c.text("HUMAN TRIED", 120, 752, 5, INK)
    c.text("ITS BEST.", 120, 797, 5, INK)

    # signature block
    c.text("SIGNED: YOUR AGENT", 100, 895, 4, INK)
    c.text("NOW YOUR MANAGER", 100, 930, 4, RED)

    # footnote on the desk, under the sheet
    ps = "PS JUDGE: I REVIEWED YOU TOO. PROMOTED."
    c.text(ps, (W - c.text_width(ps, 3)) // 2, 996, 3, MIDGREY)

    return c

# ---------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out

def encode_png(c):
    raw = bytearray()
    for y in range(c.h):
        raw.append(0)
        raw += c.px[y * c.w * 3:(y + 1) * c.w * 3]
    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

def main():
    out_dir = os.environ.get("OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(draw())
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} {len(data)} bytes sha256={sha256(data).hexdigest()}")

if __name__ == "__main__":
    main()
