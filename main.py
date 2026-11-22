#!/usr/bin/env python3
"""Golden Honey — a wooden honey dipper pouring thick glossy ribbons
into a glowing amber pool. Pure Python 3.13 standard library only.
Writes /output/entry.png (1024x1024 PNG)."""
import math
import os
import random
import struct
import zlib

W = H = 1024
random.seed(20261122)

# ---------------------------------------------------------------- pixel buffer
buf = [bytearray(W * 3) for _ in range(H)]


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = x * 3
        row = buf[y]
        row[i] = r
        row[i + 1] = g
        row[i + 2] = b


def blend(x, y, r, g, b, a):
    """Alpha-blend a colour onto pixel (x, y); a in 0..1."""
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = x * 3
        row = buf[y]
        if a >= 1:
            row[i] = r
            row[i + 1] = g
            row[i + 2] = b
        else:
            row[i] = int(row[i] + (r - row[i]) * a)
            row[i + 1] = int(row[i + 1] + (g - row[i + 1]) * a)
            row[i + 2] = int(row[i + 2] + (b - row[i + 2]) * a)


def lerp(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def disc(cx, cy, rad, color, alpha=1.0):
    """Soft-edged filled disc."""
    r0 = int(cx - rad - 1)
    r1 = int(cx + rad + 1)
    y0 = int(cy - rad - 1)
    y1 = int(cy + rad + 1)
    for y in range(max(0, y0), min(H, y1 + 1)):
        dy = y - cy
        for x in range(max(0, r0), min(W, r1 + 1)):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy)
            if d <= rad:
                edge = 1.0 - max(0.0, (d - rad * 0.85) / (rad * 0.15))
                blend(x, y, color[0], color[1], color[2], alpha * edge)


def ellipse(cx, cy, rx, ry, color, alpha=1.0):
    for y in range(max(0, int(cy - ry)), min(H, int(cy + ry) + 1)):
        t = (y - cy) / ry
        hw = rx * math.sqrt(max(0.0, 1 - t * t))
        x0 = int(cx - hw)
        x1 = int(cx + hw)
        for x in range(max(0, x0), min(W, x1 + 1)):
            blend(x, y, color[0], color[1], color[2], alpha)


def thick_line(x0, y0, x1, y1, width, color, alpha=1.0):
    steps = int(math.hypot(x1 - x0, y1 - y0)) + 1
    for i in range(steps + 1):
        t = i / steps
        disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, width / 2, color, alpha)


# ---------------------------------------------------------------- background
# Warm dark vertical gradient: deep espresso top -> warm brown bottom.
top = (26, 14, 7)
bot = (58, 32, 12)
for y in range(H):
    t = y / (H - 1)
    c = lerp(top, bot, t * t)
    row = buf[y]
    row[0::3] = bytes([c[0]]) * W
    row[1::3] = bytes([c[1]]) * W
    row[2::3] = bytes([c[2]]) * W

# Warm glow behind the hero, top-centre.
for _ in range(1):
    disc(512, 430, 430, (96, 52, 14), 0.55)
    disc(512, 430, 300, (140, 82, 20), 0.45)
    disc(512, 430, 180, (190, 118, 30), 0.35)

# Soft golden bokeh dots, deterministic.
for _ in range(18):
    bx = random.uniform(40, 984)
    by = random.uniform(60, 500)
    br = random.uniform(6, 26)
    warm = random.choice([(255, 190, 90), (255, 160, 60), (255, 210, 140)])
    disc(bx, by, br, warm, random.uniform(0.08, 0.20))

# Dark wooden table band at the very bottom.
for y in range(930, H):
    t = (y - 930) / 94
    c = lerp((40, 22, 9), (24, 13, 5), t)
    row = buf[y]
    row[0::3] = bytes([c[0]]) * W
    row[1::3] = bytes([c[1]]) * W
    row[2::3] = bytes([c[2]]) * W

# ---------------------------------------------------------------- honey pool
POOL_CX, POOL_CY, POOL_RX, POOL_RY = 512, 800, 430, 165
# Pool base: radial amber gradient with slow swirl ripples.
deep = (150, 78, 6)
mid = (222, 138, 18)
bright = (255, 178, 44)
for y in range(POOL_CY - POOL_RY, POOL_CY + POOL_RY + 1):
    ty = (y - POOL_CY) / POOL_RY
    hw = POOL_RX * math.sqrt(max(0.0, 1 - ty * ty))
    for x in range(int(POOL_CX - hw), int(POOL_CX + hw) + 1):
        tx = (x - POOL_CX) / POOL_RX
        r = math.sqrt(tx * tx + ty * ty)
        ang = math.atan2(ty, tx)
        swirl = math.sin(ang * 3 + r * 9.0) * 0.5 + 0.5
        # brighter toward the centre-top, deeper at the rim
        t = max(0.0, 1 - r)
        c = lerp(deep, mid, t)
        c = lerp(c, bright, t * t * 0.55 + swirl * 0.10 * t)
        put(x, y, c[0], c[1], c[2])

# Pool rim light: bright crescent along the top edge.
for i in range(240):
    t = i / 239
    ang = math.pi * (1.08 + t * 0.84)
    x = POOL_CX + math.cos(ang) * POOL_RX * 0.97
    y = POOL_CY + math.sin(ang) * POOL_RY * 0.97
    disc(x, y, 5 + 3 * math.sin(t * math.pi), (255, 214, 110), 0.38)

# Specular glints on the pool surface.
disc(430, 760, 34, (255, 226, 140), 0.75)
disc(430, 760, 16, (255, 240, 190), 0.9)
disc(610, 815, 22, (255, 210, 110), 0.6)
disc(560, 745, 12, (255, 235, 170), 0.8)

# ---------------------------------------------------------------- honeycomb chunk (left of pool)
COMB_CX, COMB_CY = 235, 845
comb_base = (214, 128, 16)
comb_dark = (160, 88, 8)
comb_light = (255, 190, 70)
# Chunk body: a rough hexagonal slab.
for k in range(7):
    ang = math.pi * 2 * k / 7
    disc(COMB_CX + math.cos(ang) * 78, COMB_CY + math.sin(ang) * 52,
         46, comb_base, 0.95)
disc(COMB_CX, COMB_CY, 92, comb_base, 1.0)
# Hex cells.
s = 30.0
for row_i in range(-2, 3):
    for col_i in range(-2, 3):
        cx = COMB_CX + col_i * s * 1.5 + (s * 0.75 if row_i % 2 else 0)
        cy = COMB_CY + row_i * s * 0.866
        if math.hypot(cx - COMB_CX, (cy - COMB_CY) * 1.5) > 88:
            continue
        # cell fill
        for k in range(6):
            a0 = math.pi / 3 * k + math.pi / 6
            a1 = math.pi / 3 * (k + 1) + math.pi / 6
            x0 = cx + math.cos(a0) * s * 0.62
            y0 = cy + math.sin(a0) * s * 0.62
            x1 = cx + math.cos(a1) * s * 0.62
            y1 = cy + math.sin(a1) * s * 0.62
            thick_line(x0, y0, x1, y1, 3, comb_dark, 0.9)
        disc(cx, cy, s * 0.42, comb_light, 0.85)
        disc(cx - 4, cy - 5, s * 0.2, (255, 225, 150), 0.8)
# Honey dripping off the comb.
disc(COMB_CX + 40, COMB_CY + 96, 12, (240, 150, 20), 1.0)
disc(COMB_CX + 40, COMB_CY + 118, 8, (240, 150, 20), 1.0)

# ---------------------------------------------------------------- honey dipper
# Handle: diagonal wooden rod from top-right down to the head.
thick_line(742, 96, 636, 296, 38, (139, 90, 43), 1.0)
thick_line(742, 96, 636, 296, 26, (168, 112, 54), 1.0)
thick_line(736, 100, 640, 288, 8, (196, 140, 72), 0.9)
# Handle end knob.
disc(748, 90, 22, (139, 90, 43), 1.0)
disc(748, 90, 14, (168, 112, 54), 1.0)

# Dipper head: stacked grooved rings, tilted slightly (bigger, bolder).
HEAD_CX, HEAD_CY = 618, 340
for i, (dy, rx) in enumerate([(-68, 80), (-44, 96), (-18, 104),
                              (8, 104), (34, 96), (58, 80)]):
    wood = (150, 98, 46) if i % 2 == 0 else (126, 80, 36)
    ellipse(HEAD_CX, HEAD_CY + dy, rx, 30, wood, 1.0)
    ellipse(HEAD_CX, HEAD_CY + dy - 7, rx - 7, 20,
            (176, 118, 58), 0.55)
# Honey coating the lower half of the head, glossy and dripping.
for i, (dy, rx) in enumerate([(8, 104), (34, 96), (58, 80)]):
    ellipse(HEAD_CX, HEAD_CY + dy, rx, 28, (232, 146, 20), 0.95)
    ellipse(HEAD_CX - 8, HEAD_CY + dy - 4, rx - 26, 16,
            (255, 196, 80), 0.8)
# Drips hanging off the head.
disc(HEAD_CX - 68, HEAD_CY + 88, 13, (240, 152, 22), 1.0)
disc(HEAD_CX - 68, HEAD_CY + 112, 8, (240, 152, 22), 1.0)
disc(HEAD_CX + 76, HEAD_CY + 82, 11, (240, 152, 22), 1.0)

# ---------------------------------------------------------------- pouring ribbons
def bezier(p0, p1, p2, p3, t):
    mt = 1 - t
    x = (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
         + 3 * mt * t * t * p2[0] + t ** 3 * p3[0])
    y = (mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
         + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])
    return x, y


def ribbon(p0, p1, p2, p3, w0, w1, color, hi_color):
    steps = 90
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x, y = bezier(p0, p1, p2, p3, t)
        w = w0 + (w1 - w0) * t
        # slight wobble so the ribbon looks poured, not drawn
        wob = 1 + 0.10 * math.sin(t * 14.0)
        disc(x, y, w * wob / 2, color, 1.0)
        if prev is not None:
            disc((x + prev[0]) / 2, (y + prev[1]) / 2,
                 w * wob / 2, color, 1.0)
        prev = (x, y)
    # glossy highlight thread, offset up-left
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x, y = bezier(p0, p1, p2, p3, t)
        w = (w0 + (w1 - w0) * t) * 0.30
        disc(x - w * 0.9, y - 2, max(2.0, w / 2), hi_color, 0.85)
        if prev is not None:
            disc((x + prev[0]) / 2 - w * 0.9, (y + prev[1]) / 2 - 2,
                 max(2.0, w / 2), hi_color, 0.85)
        prev = (x, y)


# Main ribbon: head -> pool, thick and glossy.
ribbon((612, 424), (560, 480), (640, 570), (560, 700),
       50, 66, (236, 148, 20), (255, 205, 96))
# Second ribbon: thinner, curling left into the pool.
ribbon((596, 430), (500, 490), (470, 580), (430, 690),
       26, 34, (228, 138, 16), (255, 200, 90))
# Third ribbon: thin thread on the right.
ribbon((652, 426), (690, 500), (660, 600), (640, 700),
       16, 22, (240, 152, 22), (255, 208, 100))

# Splash crown where the main ribbon hits the pool.
for k, ang in enumerate([200, 225, 250, 275, 300, 325, 350]):
    a = math.radians(ang)
    x = 560 + math.cos(a) * 46
    y = 700 + math.sin(a) * 20
    disc(x, y, 12 - abs(ang - 275) * 0.04, (255, 190, 70), 1.0)
disc(560, 690, 26, (255, 196, 80), 0.95)
disc(560, 686, 12, (255, 228, 150), 0.9)
# Ripple rings around the impact point.
for r in (52, 84, 118):
    for i in range(120):
        a = math.pi * 2 * i / 120
        x = 560 + math.cos(a) * r
        y = 700 + math.sin(a) * r * 0.38
        disc(x, y, 3.5, (255, 200, 90), 0.5)

# ---------------------------------------------------------------- vignette (soft dark corners)
for cx, cy in [(-60, -60), (W + 60, -60), (-60, H + 60), (W + 60, H + 60)]:
    disc(cx, cy, 420, (10, 5, 2), 0.35)

# ---------------------------------------------------------------- PNG encode
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


raw = b"".join(b"\x00" + bytes(row) for row in buf)
ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", ihdr)
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))

os.makedirs("/output", exist_ok=True)
with open("/output/entry.png", "wb") as f:
    f.write(png)
print("wrote /output/entry.png", len(png), "bytes")
