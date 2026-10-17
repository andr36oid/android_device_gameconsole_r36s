#!/usr/bin/env python3
"""Procedural boot logo generator for andr36oid.

Usage: gen-logo.py [-w W] [-H H] [-o out.bmp] [--png preview.png] [--title S] [--subtitle S] [--build 2026-09-10]

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
LINEAGE = (0x16, 0x7C, 0x80)   # LineageOS teal
HEART = (0xA4, 0x38, 0x46)     # muted red, still readable on black


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
    for i, ch in enumerate(s):
        # Prefix lengths retain the font's kerning between adjacent letters.
        advance = text_w(f, s[:i + 1]) - text_w(f, ch) + i * track
        d.text((x + advance, y), ch, font=f, fill=fill, anchor="ls")
    return tracked_w(f, s, track)


def tracked_w(f, s, track):
    return text_w(f, s) + track * max(0, len(s) - 1)


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


def heart(d, x, baseline, size, fill):
    """Heart glyph, left edge at x, sitting on the baseline. Returns advance width."""
    top = baseline - size
    r = size / 4
    cx = x + size / 2
    disc(d, cx - r, top + r, r, fill)
    disc(d, cx + r, top + r, r, fill)
    d.polygon([(cx - 2 * r, top + r), (cx, top + 2 * r * 0.55), (cx + 2 * r, top + r), (cx, baseline)], fill=fill)
    return size


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


def draw_wordmark(d, w, h, u, title, subtitle, credits, fg=WHITE, light=LIGHT, dim=DIM):
    """Title, the credits line above it and the subtitle, centred as on the boot logo."""
    # ---- title
    size = 0.20 * u
    track = 0.005 * u
    f_t = font("Roboto-Bold.ttf", size)
    tw = tracked_w(f_t, title, track)
    if tw > 0.84 * w:                      # cap title width on narrow/square screens
        k = 0.84 * w / tw
        size, track = size * k, track * k
        f_t = font("Roboto-Bold.ttf", size)
        tw = tracked_w(f_t, title, track)
    tx = (w - tw) / 2
    ty = h * 0.46
    draw_tracked(d, f_t, (tx, ty), title, track, fg)

    # ---- credits, centred right above the title, monospace
    if credits:
        # "prefix from name1 - name2 - name3": names bold, hyphens as middle dots, "<3" as a heart
        f_c = font("DejaVuSansMono.ttf", 0.036 * u)
        f_cb = font("DejaVuSansMono-Bold.ttf", 0.036 * u)
        hs = cap_h(f_c) * 1.15
        prefix, _, names = credits.rpartition(" from ")
        segs = []
        if names:
            for i, tok in enumerate((prefix + " from").split(" ")):
                if i:
                    segs.append((" ", f_c))
                segs.append((None, hs) if tok == "<3" else (tok, f_c))
            segs.append((" ", f_c))
        for i, n in enumerate((names or credits).split(" - ")):
            if i:
                segs.append((" \u00b7 ", f_c))
            segs.append((n, f_cb))
        total = sum(f if t is None else text_w(f, t) for t, f in segs)
        cy = ty - cap_h(f_t) - 0.045 * u
        x = (w - total) / 2
        for txt, f in segs:
            if txt is None:
                x += heart(d, x, cy, f, HEART)
            else:
                d.text((x, cy), txt, font=f, fill=dim, anchor="ls")
                x += text_w(f, txt)

    # ---- subtitle, right-aligned to title
    f_s = font("Roboto-Light.ttf", 0.058 * u)
    d.text((tx + tw, ty + 0.045 * u + cap_h(f_s)), subtitle, font=f_s, fill=light, anchor="rs")
    return tx, tw


def draw_lineage(d, x, base_y, u, k, R, f_lo, f_lp, line, bg, fg=LINEAGE):
    """The Lineage mark, "LineageOS" and a small line above it, left edge at x."""
    mark_cx = x + 2.1 * R
    text_x = x + 4.2 * R + 0.025 * u * k
    lineage_mark(d, mark_cx, base_y - 0.5 * cap_h(f_lo) - 0.2 * R, R, fg, bg)
    d.text((text_x, base_y), "LineageOS", font=f_lo, fill=fg, anchor="ls")
    d.text((text_x, base_y - cap_h(f_lo) - 0.020 * u * k), line, font=f_lp, fill=fg, anchor="ls")


def cropped_logo(im, ss):
    """Leave room for the downsampling filter around transparent artwork."""
    left, top, right, bottom = im.getbbox()
    pad = 4 * ss
    im = im.crop((max(0, left - pad), max(0, top - pad),
                  min(im.width, right + pad), min(im.height, bottom + pad)))
    return im.resize((round(im.width / ss), round(im.height / ss)), Image.LANCZOS)


def setup_wizard(out_dir, credits, ss=4):
    """The setup wizard's first and last screen: the wordmark on a transparent
    background, white for dark mode and dark grey for light mode, and the small
    "Based on LineageOS" for the lower left corner. Cropped to what is drawn."""
    w, h = 640 * ss, 480 * ss
    u = min(w, h)
    for name, fg, light, dim in (("drawable-night-nodpi", WHITE, LIGHT, DIM),
                                 ("drawable-nodpi", (0x20, 0x21, 0x24), (0x3C, 0x40, 0x43), (0x70, 0x75, 0x7A))):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_wordmark(ImageDraw.Draw(im), w, h, u, "andr36oid", "RK3326 Community", credits, fg, light, dim)
        im = cropped_logo(im, ss)
        os.makedirs(os.path.join(out_dir, name), exist_ok=True)
        im.save(os.path.join(out_dir, name, "andr36oid_logo.png"))
    # the lineage mark punches its rings out with the background colour: draw on
    # black, then use a white mask as alpha so solid teal stays fully opaque
    R = 0.038 * u
    f_lo = font("Roboto-Medium.ttf", 0.070 * u)
    f_lp = font("Roboto-Regular.ttf", 0.040 * u)
    im = Image.new("RGB", (w, h), BLACK)
    draw_lineage(ImageDraw.Draw(im), 0.1 * u, 0.5 * h, u, 1.0, R, f_lo, f_lp,
                 "Based on", BLACK, WHITE)
    alpha = im.convert("L")
    teal = Image.new("RGBA", (w, h), LINEAGE + (255,))
    teal.putalpha(alpha)
    teal = cropped_logo(teal, ss)
    teal.save(os.path.join(out_dir, "drawable-nodpi", "based_on_lineageos.png"))
    print(f"wrote the setup wizard logos to {out_dir}")


def render(W, H, title, subtitle, build="", credits="", ss=4, turn=False):
    w, h = W * ss, H * ss
    u = min(w, h)
    im = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(im)

    margin = 0.07 * u

    tx, tw = draw_wordmark(d, w, h, u, title, subtitle, credits)

    # ---- build number, top right, monospace
    if build:
        f_b = font("DejaVuSansMono.ttf", 0.036 * u)
        # U-Boot prints its version at the upper left. Keep a long label in the
        # right half, and leave room there after rotating a sideways panel too.
        build_margin = max(margin, 0.20 * u) if turn else margin
        max_width = min(0.42 * w, w - build_margin - 0.52 * w)
        if text_w(f_b, build) > max_width:
            f_b = font("DejaVuSansMono.ttf", 0.036 * u * max_width / text_w(f_b, build))
        d.text((w - build_margin, margin + cap_h(f_b)), build, font=f_b, fill=DIM, anchor="rs")

    # ---- footer blocks; shrink both if they would collide on narrow screens
    def footer(k):
        f_pb = font("Roboto-Regular.ttf", 0.040 * u * k)
        f_an = font("Roboto-Medium.ttf", 0.080 * u * k)
        f_lo = font("Roboto-Medium.ttf", 0.070 * u * k)
        f_lp = font("Roboto-Regular.ttf", 0.040 * u * k)
        head_r = 0.038 * u * k
        R = 0.038 * u * k
        an_block = text_w(f_an, "android") + 0.022 * u * k + 2 * head_r
        lo_block = 4.2 * R + 0.025 * u * k + text_w(f_lo, "LineageOS")
        return f_pb, f_an, f_lo, f_lp, head_r, R, an_block, lo_block

    k = 1.0
    f_pb, f_an, f_lo, f_lp, head_r, R, an_block, lo_block = footer(k)
    avail = w - 2 * margin - 0.08 * u
    if an_block + lo_block > avail:
        k = avail / (an_block + lo_block)
        f_pb, f_an, f_lo, f_lp, head_r, R, an_block, lo_block = footer(k)

    base_y = h - margin

    # Based on android (bottom right), grey except the bugdroid
    head_cx = w - margin - head_r
    an_x = head_cx - head_r - 0.022 * u * k - text_w(f_an, "android")
    bugdroid(d, head_cx, base_y - 0.004 * u, head_r, GREEN, WHITE, BLACK)
    d.text((an_x, base_y), "android", font=f_an, fill=DIM, anchor="ls")
    d.text((an_x, base_y - cap_h(f_an) - 0.020 * u * k), "Based on", font=f_pb, fill=DIM, anchor="ls")

    # Powered by LineageOS (bottom left), Lineage teal
    draw_lineage(d, margin, base_y, u, k, R, f_lo, f_lp, "Powered by", BLACK)

    return im.resize((W, H), Image.LANCZOS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", "--width", type=int, default=640)
    p.add_argument("-H", "--height", type=int, default=480)
    p.add_argument("-o", "--out", default=os.path.join(HERE, "logo.bmp"))
    p.add_argument("--png")
    p.add_argument("--title", default="andr36oid")
    p.add_argument("--subtitle", default="RK3326 Community")
    p.add_argument("--build", default="", help="build number, ISO date e.g. 2026-09-10 (omit to hide)")
    p.add_argument("--credits", default="with <3 from snaccy - kenny - kauan",
                   help='"<prefix> from a - b - c"; names go bold, hyphens become middle dots, <3 becomes a heart ("" to hide)')
    p.add_argument("--turn", action="store_true",
                   help="panel mounted sideways: draw W x H, store it turned a quarter anticlockwise")
    p.add_argument("--setup-wizard", metavar="RES_DIR",
                   help="instead: the setup wizard's logo PNGs into RES_DIR (packages/apps/SetupWizard/res)")
    a = p.parse_args()
    if a.setup_wizard:
        setup_wizard(a.setup_wizard, a.credits)
        return

    im = render(a.width, a.height, a.title, a.subtitle, a.build, a.credits, turn=a.turn)
    if a.turn:
        im = im.rotate(90, expand=True)
    im.save(a.out, "BMP")
    if a.png:
        im.save(a.png, "PNG")
    print(f"wrote {a.out} ({a.width}x{a.height})" + (f" + {a.png}" if a.png else ""))


if __name__ == "__main__":
    main()
