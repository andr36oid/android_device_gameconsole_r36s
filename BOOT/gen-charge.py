#!/usr/bin/env python3
"""Charge screen images for U-Boot's charge animation.

Usage: gen-charge.py [-w W] [-H H] [-o outdir] [--png]

When a charger is plugged in and the console is off (or is switched on while
plugged in), U-Boot stays in its charge loop and loads these files from the
root of BOOT (drivers/power/charge_animation.c, CONFIG_PLATFORM_ODROID_GOADV):

  battery_0.bmp  below 60 %      battery_2.bmp  80-99 %
  battery_1.bmp  60-79 %         battery_3.bmp  100 %
  battery_fail.bmp  too low to start

It shows them one after another from the current level up to full, 0.8 s each.
The decoder copies rows straight into the framebuffer, so the images must be
24-bit, uncompressed and exactly as wide as the screen. On 720x720 screens
U-Boot prints the battery voltage and current in the bottom 32 rows, so that
strip stays black. Requires Pillow.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 220)
DIM = (135, 135, 135)
GREEN = (0x3D, 0xDC, 0x84)
RED = (0xE0, 0x40, 0x40)

LEVELS = 4          # battery_0 .. battery_3 fill 1 .. 4 segments


def font(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), int(round(px)))


def render(W, H, filled, fail, ss=4):
    w, h = W * ss, H * ss
    # 720x720: U-Boot's voltage/current lines sit at 688-720, keep them clear
    usable_h = h - 48 * ss if H >= 720 else h
    u = min(w, usable_h)
    im = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(im)
    cx = w / 2

    # battery body, centred a little above the middle
    bw, bh = 0.62 * u, 0.26 * u
    line = 0.018 * u
    x0 = cx - bw / 2
    y0 = usable_h * 0.40 - bh / 2
    edge = RED if fail else LIGHT
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=0.03 * u, outline=edge, width=int(line))
    tip_w, tip_h = 0.04 * u, 0.11 * u
    d.rounded_rectangle([x0 + bw + line / 2, y0 + bh / 2 - tip_h / 2,
                         x0 + bw + line / 2 + tip_w, y0 + bh / 2 + tip_h / 2],
                        radius=0.01 * u, fill=edge)

    # segments
    pad = line + 0.02 * u
    gap = 0.02 * u
    sw = (bw - 2 * pad - (LEVELS - 1) * gap) / LEVELS
    for i in range(LEVELS):
        sx = x0 + pad + i * (sw + gap)
        box = [sx, y0 + pad, sx + sw, y0 + bh - pad]
        if not fail and i < filled:
            d.rectangle(box, fill=GREEN)
        elif fail and i == 0:
            d.rectangle([box[0], box[1], box[0] + sw * 0.3, box[3]], fill=RED)

    # text
    f_big = font("Roboto-Medium.ttf", 0.085 * u)
    f_txt = font("Roboto-Regular.ttf", 0.050 * u)
    ty = y0 + bh + 0.16 * u
    if fail:
        d.text((cx, ty), "Battery too low to start", font=f_big, fill=RED, anchor="ms")
        lines = ["Leave the charger plugged in.",
                 "The screen turns off in a few seconds."]
    else:
        d.text((cx, ty), "Charging", font=f_big, fill=WHITE, anchor="ms")
        lines = ["Hold POWER for 2 seconds to start.",
                 "Press POWER to turn the screen on or off.",
                 "Unplug the charger to switch off."]
    ly = ty + 0.11 * u
    for i, s in enumerate(lines):
        d.text((cx, ly), s, font=f_txt, fill=LIGHT if i == 0 else DIM, anchor="ms")
        ly += 0.075 * u

    return im.resize((W, H), Image.LANCZOS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", "--width", type=int, default=640)
    p.add_argument("-H", "--height", type=int, default=480)
    p.add_argument("-o", "--outdir", default=".")
    p.add_argument("--png", action="store_true", help="also write .png previews")
    a = p.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    frames = [("battery_%d" % i, i + 1, False) for i in range(LEVELS)]
    frames.append(("battery_fail", 0, True))
    for name, filled, fail in frames:
        im = render(a.width, a.height, filled, fail)
        im.save(os.path.join(a.outdir, name + ".bmp"), "BMP")
        if a.png:
            im.save(os.path.join(a.outdir, name + ".png"), "PNG")
    print(f"wrote {len(frames)} charge images ({a.width}x{a.height}) to {a.outdir}")


if __name__ == "__main__":
    main()
