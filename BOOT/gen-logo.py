#!/usr/bin/env python3
"""Procedural boot logo generator for andr36oid.

Usage: gen-logo.py [-w W] [-H H] [-o out.bmp] [--png preview.png] [--title S] [--subtitle S]

Layout is relative to the shorter screen edge so any resolution works.
Renders at 4x and downsamples for anti-aliasing. Output: 24-bit BMP for U-Boot.
Requires Pillow.
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 220)
DIM = (135, 135, 135)
GREEN = (0x3D, 0xDC, 0x84)


def font(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), int(round(px)))


def text_w(f, s):
    return f.getlength(s)


def asc(f):
    return f.getmetrics()[0]


def cap_h(f):
    b = f.getbbox("H")
    return b[3] - b[1]


def draw_tracked(d, f, xy, s, track, fill):
    """Draw text with letter spacing, anchored at left baseline. Returns width."""
    x, y = xy
    x0 = x
    for i, ch in enumerate(s):
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += text_w(f, ch) + (track if i < len(s) - 1 else 0)
    return x - x0


def tracked_w(f, s, track):
    return sum(text_w(f, c) for c in s) + track * (len(s) - 1)


def fat_line(d, p1, p2, t, fill):
    d.line([p1, p2], fill=fill, width=int(round(t)))
    for x, y in (p1, p2):
        d.ellipse([x - t / 2, y - t / 2, x + t / 2, y + t / 2], fill=fill)


def disc(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def ring(d, cx, cy, ro, ri, fill, bg):
    disc(d, cx, cy, ro, fill)
    if ri > 0:
        disc(d, cx, cy, ri, bg)


def lineage_mark(d, cx, cy, R, fill, bg):
    """LineageOS mark. R = centre-ring radius. ~4.2R wide, ~2.5R tall."""
    sx, sy = 1.55 * R, 0.55 * R
    fat_line(d, (cx, cy), (cx - sx, cy + sy), 0.22 * R, fill)
    fat_line(d, (cx, cy), (cx + sx, cy + sy), 0.22 * R, fill)
    ring(d, cx, cy, R, 0.72 * R, fill, bg)
    disc(d, cx, cy, 0.35 * R, fill)
    ring(d, cx - sx, cy + sy, 0.45 * R, 0.22 * R, fill, bg)
    ring(d, cx + sx, cy + sy, 0.45 * R, 0.22 * R, fill, bg)


def bugdroid(d, cx, cy, r, green, white, bg):
    """Android head. r = radius, (cx, cy) = centre of the flat base."""
    disc(d, cx, cy, r, green)
    d.rectangle([cx - r - 2, cy, cx + r + 2, cy + r + 2], fill=bg)
    for s in (-1, 1):
        a = math.radians(90 - s * 32)
        p1 = (cx + math.cos(a) * r * 0.78, cy - math.sin(a) * r * 0.78)
        p2 = (cx + math.cos(a) * r * 1.30, cy - math.sin(a) * r * 1.30)
        fat_line(d, p1, p2, 0.11 * r, green)
        disc(d, cx + s * 0.42 * r, cy - 0.42 * r, 0.10 * r, white)


def render(W, H, title, subtitle, ss=4):
    w, h = W * ss, H * ss
    u = min(w, h)
    im = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(im)

    margin = 0.07 * u

    # ---- title
    size = 0.20 * u
    track = 0.008 * u
    f_t = font("Roboto-Bold.ttf", size)
    tw = tracked_w(f_t, title, track)
    if tw > 0.84 * w:                      # cap title width on narrow/square screens
        k = 0.84 * w / tw
        size, track = size * k, track * k
        f_t = font("Roboto-Bold.ttf", size)
        tw = tracked_w(f_t, title, track)
    tx = (w - tw) / 2
    ty = h * 0.46
    draw_tracked(d, f_t, (tx, ty), title, track, WHITE)

    # ---- subtitle, right-aligned to title
    f_s = font("Roboto-Light.ttf", 0.066 * u)
    d.text((tx + tw, ty + 0.045 * u + cap_h(f_s)), subtitle, font=f_s, fill=LIGHT, anchor="rs")

    # ---- Powered by android (bottom right)
    f_pb = font("Roboto-Regular.ttf", 0.040 * u)
    f_an = font("Roboto-Medium.ttf", 0.080 * u)
    head_r = 0.038 * u
    base_y = h - margin
    head_cx = w - margin - head_r
    an_w = text_w(f_an, "android")
    an_x = head_cx - head_r - 0.022 * u - an_w
    bugdroid(d, head_cx, base_y - 0.004 * u, head_r, GREEN, WHITE, BLACK)
    d.text((an_x, base_y), "android", font=f_an, fill=WHITE, anchor="ls")
    d.text((an_x, base_y - cap_h(f_an) - 0.020 * u), "Powered by", font=f_pb, fill=LIGHT, anchor="ls")

    # ---- Powered by LineageOS (bottom left, dimmed)
    f_lo = font("Roboto-Regular.ttf", 0.050 * u)
    f_lp = font("Roboto-Light.ttf", 0.034 * u)
    R = 0.030 * u
    mark_cx = margin + 2.1 * R
    text_x = margin + 4.2 * R + 0.025 * u
    lineage_mark(d, mark_cx, base_y - 0.5 * cap_h(f_lo) - 0.2 * R, R, DIM, BLACK)
    d.text((text_x, base_y), "LineageOS", font=f_lo, fill=DIM, anchor="ls")
    d.text((text_x, base_y - cap_h(f_lo) - 0.016 * u), "Powered by", font=f_lp, fill=DIM, anchor="ls")

    return im.resize((W, H), Image.LANCZOS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", "--width", type=int, default=640)
    p.add_argument("-H", "--height", type=int, default=480)
    p.add_argument("-o", "--out", default=os.path.join(HERE, "logo.bmp"))
    p.add_argument("--png")
    p.add_argument("--title", default="andr36oid")
    p.add_argument("--subtitle", default="RK3326 Community")
    a = p.parse_args()

    im = render(a.width, a.height, a.title, a.subtitle)
    im.save(a.out, "BMP")
    if a.png:
        im.save(a.png, "PNG")
    print(f"wrote {a.out} ({a.width}x{a.height})" + (f" + {a.png}" if a.png else ""))


if __name__ == "__main__":
    main()
