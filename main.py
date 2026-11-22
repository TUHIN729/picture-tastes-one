#!/usr/bin/env python3
"""Golden Hour Strawberry — one ripe strawberry on a cream plate.

Pure Python 3.13 standard library. Draws a 1024x1024 PNG to
/output/entry.png. Deterministic: fixed seed, no time, no network.
"""
import math
import random
import struct
import zlib

W = H = 1024
RNG = random.Random(20261123)

# ---------- pixel buffer ----------
buf = bytearray(W * H * 3)


def put(x, y, r, g, b, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        if a >= 1.0:
            buf[i], buf[i + 1], buf[i + 2] = int(r), int(g), int(b)
        else:
            buf[i] = int(buf[i] * (1 - a) + r * a)
            buf[i + 1] = int(buf[i + 1] * (1 - a) + g * a)
            buf[i + 2] = int(buf[i + 2] * (1 - a) + b * a)


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def ellipse(cx, cy, rx, ry, color, a=1.0, soft=0.0):
    """Filled ellipse with optional soft edge (feather in px)."""
    x0 = max(0, int(cx - rx - soft - 1))
    x1 = min(W - 1, int(cx + rx + soft + 1))
    y0 = max(0, int(cy - ry - soft - 1))
    y1 = min(H - 1, int(cy + ry + soft + 1))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            d = dx * dx + dy * dy
            if d <= 1.0:
                aa = a
                if soft > 0:
                    edge = 1.0 - d
                    aa = a * min(1.0, edge * (rx + ry) / 2 / max(soft, 1))
                put(x, y, *color, a=aa)


def vgrad_ellipse(cx, cy, rx, ry, top, bot, soft=0.0):
    """Vertical-gradient ellipse."""
    x0 = max(0, int(cx - rx - soft - 1))
    x1 = min(W - 1, int(cx + rx + soft + 1))
    y0 = max(0, int(cy - ry - soft - 1))
    y1 = min(H - 1, int(cy + ry + soft + 1))
    for y in range(y0, y1 + 1):
        t = (y - (cy - ry)) / (2 * ry)
        col = tuple(lerp(top[k], bot[k], t) for k in range(3))
        dy = (y - cy) / ry
        for x in range(x0, x1 + 1):
            dx = (x - cx) / rx
            d = dx * dx + dy * dy
            if d <= 1.0:
                aa = 1.0
                if soft > 0:
                    aa = min(1.0, (1.0 - d) * (rx + ry) / 2 / max(soft, 1))
                put(x, y, *col, a=aa)


# ---------- background: dark warm wood ----------
for y in range(H):
    t = y / H
    base = (
        lerp(58, 30, t),
        lerp(38, 20, t),
        lerp(24, 13, t),
    )
    for x in range(W):
        # soft warm light pool from upper left
        dx = (x - 380) / 700
        dy = (y - 300) / 700
        glow = max(0.0, 1.0 - (dx * dx + dy * dy)) * 26
        put(x, y, base[0] + glow, base[1] + glow * 0.7, base[2] + glow * 0.4)

# wood grain: faint horizontal streaks
for _ in range(240):
    gx = RNG.randint(0, W - 1)
    gy = RNG.randint(0, H - 1)
    gl = RNG.randint(40, 260)
    gb = RNG.choice([-14, -10, 10, 14])
    for s in range(gl):
        xx = gx + s
        if xx >= W:
            break
        put(xx, gy, clamp(46 + gb), clamp(30 + gb * 0.7), clamp(19 + gb * 0.5), a=0.25)

# plank seams
for sy in (300, 620, 900):
    for x in range(W):
        put(x, sy, 12, 8, 5, a=0.55)
        put(x, sy + 1, 60, 40, 24, a=0.25)

# ---------- plate shadow + plate ----------
ellipse(512, 700, 400, 150, (10, 6, 4), a=0.55, soft=26)
vgrad_ellipse(512, 660, 385, 150, (252, 246, 232), (214, 200, 178), soft=4)
ellipse(512, 660, 385, 150, (255, 255, 250), a=0.18, soft=30)
# plate rim
for k in range(6):
    ry = 150 - k * 3
    ellipse(512, 660, 385 - k * 2, ry, (196, 182, 160), a=0.10, soft=2)

# ---------- strawberry body ----------
# profile: wide shoulders, tapering to a soft point at the bottom
CX, TOP, BOT = 512, 300, 830
SH = 250  # half-width at shoulders


def half_width(y):
    t = (y - TOP) / (BOT - TOP)  # 0 top .. 1 bottom
    if t < 0 or t > 1:
        return 0.0
    # rounded shoulders: rise fast from a narrow crown, full width near
    # t=0.45, then taper to a soft point at the bottom
    rise = math.sin(math.pi / 2 * min(1.0, t * 2.2)) ** 0.8
    taper = 1.0 - max(0.0, (t - 0.5) / 0.5) ** 2.0 * 0.98
    return SH * rise * taper


for y in range(TOP, BOT + 1):
    hw = half_width(y)
    if hw <= 0:
        continue
    t = (y - TOP) / (BOT - TOP)
    # vertical gradient: bright lit red -> deep crimson
    r = lerp(238, 150, t)
    g = lerp(64, 18, t)
    b = lerp(52, 22, t)
    # horizontal shading: light from upper left, shadow right edge
    for x in range(int(CX - hw), int(CX + hw) + 1):
        u = (x - (CX - hw)) / max(1.0, 2 * hw)  # 0 left .. 1 right
        shade = 1.0 - 0.35 * max(0.0, (u - 0.55) / 0.45)
        lit = 1.0 + 0.22 * max(0.0, 1.0 - abs(u - 0.28) * 3.2)
        put(x, y, clamp(r * shade * lit), clamp(g * shade * lit),
            clamp(b * shade * lit))

# seeds: small pale achenes in staggered rows on the body, with a
# little jitter so they read as organic, not printed
seed_rng = random.Random(777)
for row in range(11):
    y = TOP + 55 + row * 44
    n = 9 - abs(row - 4) // 2
    for k in range(n):
        fx = (k + 0.5) / n + (0.03 if row % 2 else -0.03)
        jx = seed_rng.uniform(-5, 5)
        jy = seed_rng.uniform(-4, 4)
        x = CX + (fx - 0.5) * 2 * half_width(y) * 0.88 + jx
        y2 = y + jy
        if abs(x - CX) > half_width(y2) - 14:
            continue
        # seed dimple shadow then pale seed
        ellipse(x + 1, y2 + 2, 7, 10, (120, 20, 16), a=0.6, soft=3)
        ellipse(x, y2, 6, 9, (250, 226, 170), a=0.95, soft=2)
        ellipse(x - 2, y2 - 3, 2, 3, (255, 248, 220), a=0.9, soft=1)

# gloss highlight on the upper-left curve (small, tight, glossy)
ellipse(430, 420, 70, 42, (255, 210, 200), a=0.22, soft=26)
ellipse(420, 402, 34, 18, (255, 240, 235), a=0.38, soft=12)
# second smaller gloss lower right
ellipse(600, 620, 60, 34, (255, 190, 175), a=0.16, soft=22)

# ---------- calyx: green leaves fanning from the top ----------
LEAF = (46, 122, 44)
LEAF_D = (28, 84, 30)


def leaf(x0, y0, x1, y1, x2, y2, col):
    """Filled triangle leaf with a soft edge."""
    minx, maxx = max(0, min(x0, x1, x2)), min(W - 1, max(x0, x1, x2))
    miny, maxy = max(0, min(y0, y1, y2)), min(H - 1, max(y0, y1, y2))
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if den == 0:
        return
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            a1 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / den
            a2 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / den
            a3 = 1 - a1 - a2
            if a1 >= 0 and a2 >= 0 and a3 >= 0:
                put(x, y, *col, a=0.97)


leaf(512, 322, 388, 262, 462, 336, LEAF)
leaf(512, 322, 636, 262, 562, 336, LEAF_D)
leaf(512, 322, 462, 232, 496, 316, LEAF_D)
leaf(512, 322, 562, 230, 530, 316, LEAF)
leaf(512, 322, 512, 214, 540, 312, LEAF_D)
# short angled stem stub
for s in range(26):
    put(512 + s // 2, 216 - s // 2, 96, 128, 60, a=0.95)
    put(513 + s // 2, 216 - s // 2, 70, 96, 44, a=0.9)

# ---------- juice droplets on the plate ----------
for (dx, dy, dr) in ((330, 700, 9), (700, 720, 7), (660, 690, 5), (360, 740, 6)):
    ellipse(dx, dy, dr, int(dr * 0.7), (235, 120, 90), a=0.55, soft=3)
    ellipse(dx - 2, dy - 2, 2, 2, (255, 220, 200), a=0.8, soft=1)

# ---------- vignette ----------
for y in range(H):
    for x in range(W):
        dx = (x - W / 2) / (W / 2)
        dy = (y - H / 2) / (H / 2)
        d = dx * dx + dy * dy
        if d > 0.75:
            dark = min(0.42, (d - 0.75) * 0.55)
            i = (y * W + x) * 3
            buf[i] = int(buf[i] * (1 - dark))
            buf[i + 1] = int(buf[i + 1] * (1 - dark))
            buf[i + 2] = int(buf[i + 2] * (1 - dark))

# ---------- PNG encode (stdlib only) ----------
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
raw = bytearray()
for y in range(H):
    raw.append(0)
    raw += buf[y * W * 3:(y + 1) * W * 3]
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")

import os
os.makedirs("/output", exist_ok=True)
with open("/output/entry.png", "wb") as f:
    f.write(png)
print("wrote /output/entry.png", len(png), "bytes")
