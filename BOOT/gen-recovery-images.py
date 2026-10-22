#!/usr/bin/env python3
"""andr36oid's pictures for recovery, in place of Lineage's.

Usage: gen-recovery-images.py <bootable/recovery>/res-mdpi/images

logo_image.png (and logo_image_switch.png): the wordmark with "Recovery" under it,
256x160 like Lineage's, over the menu. loop00000-00029.png: the animation while
recovery works, 200x200, an arc going round "36". Drawn with gen-logo.py's fonts.
"""
import importlib.util
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("genlogo", os.path.join(HERE, "gen-logo.py"))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

SS = 4
FRAMES = 30


def logo():
    w, h = 256 * SS, 160 * SS
    im = Image.new("RGB", (w, h), g.BLACK)
    g.draw_wordmark(ImageDraw.Draw(im), w, h, min(w, h) * 1.6, "andr36oid", "Recovery", "")
    return im.resize((256, 160), Image.LANCZOS)


def frame(i):
    s = 200 * SS
    im = Image.new("RGB", (s, s), g.BLACK)
    d = ImageDraw.Draw(im)
    c, r, t = s / 2, s * 0.40, s * 0.035
    box = (c - r, c - r, c + r, c + r)
    d.ellipse(box, outline=(0x30, 0x30, 0x30), width=int(t))
    start = i * 360 / FRAMES - 90
    d.arc(box, start, start + 100, fill=g.LIGHT, width=int(t))
    f = g.font("Roboto-Bold.ttf", s * 0.30)
    d.text((c, c), "36", font=f, fill=g.WHITE, anchor="mm")
    return im.resize((200, 200), Image.LANCZOS)


def main():
    out = sys.argv[1]
    im = logo()
    for name in ("logo_image.png", "logo_image_switch.png"):
        im.save(os.path.join(out, name))
    for i in range(FRAMES):
        frame(i).save(os.path.join(out, "loop%05d.png" % i))


if __name__ == "__main__":
    main()
