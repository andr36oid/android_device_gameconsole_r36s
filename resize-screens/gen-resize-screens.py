#!/usr/bin/env python3
"""Screens for the first-boot resizer, in English, Spanish and Portuguese.

Usage: gen-resize-screens.py [-w W] [-H H] -o out.cpio.gz [--png-dir DIR]

The resizer (common/resizing, Image-resizing with its own built-in ramdisk)
shows /resizing_480.ppm while it makes userdata and EASYROMS, and
/resized_480.ppm before it restarts into Android. Its pictures are English
only and 640x480 on every screen. This draws both screens at W x H and packs
them into a small gzip cpio with those two names. BOOT/boot.ini hands it to
Image-resizing as an extra ramdisk, and the kernel unpacks it over the built-in
one, so the resizer shows these files instead. Image-resizing isn't rebuilt.

The console can't know the language yet, so the three languages are stacked.
Requires Pillow. Fonts: BOOT/fonts (the ones gen-logo.py uses).
"""
import argparse
import gzip
import io
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "BOOT", "fonts")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (170, 170, 170)
RED = (0xE0, 0x40, 0x40)
GREEN = (0x3D, 0xDC, 0x84)

# (title, detail) per language: English, Spanish, Portuguese (Brazil)
SCREENS = {
    "resizing_480.ppm": [
        ("Preparing the SD card", "1-2 minutes. Don't turn the console off."),
        ("Preparando la tarjeta SD", "1-2 minutos. No apagues la consola."),
        ("Preparando o cartão SD", "1-2 minutos. Não desligue o console."),
    ],
    "resized_480.ppm": [
        ("SD card ready, restarting", "The first start takes a few more minutes."),
        ("Tarjeta SD lista, reiniciando", "El primer inicio tarda unos minutos más."),
        ("Cartão SD pronto, reiniciando", "A primeira inicialização leva mais alguns minutos."),
    ],
}


def font(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), int(round(px)))


def cap_h(f):
    b = f.getbbox("H")
    return b[3] - b[1]


def power_icon(d, cx, cy, r, color, crossed):
    """Power symbol (IEC 5009), optionally crossed out: "don't turn off"."""
    t = max(2, r * 0.22)
    # ring with a gap at the top
    d.arc([cx - r, cy - r, cx + r, cy + r], start=-60, end=240, fill=color, width=int(round(t)))
    d.line([(cx, cy - r * 1.15), (cx, cy - r * 0.05)], fill=color, width=int(round(t)))
    if crossed:
        k = r * 1.35
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=RED, width=int(round(t * 1.1)))


def sd_icon(d, cx, cy, h, color):
    """SD card outline with the cut corner and contacts."""
    w = h * 0.78
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    c = w * 0.3
    t = max(2, h * 0.07)
    pts = [(x0 + c, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + c), (x0 + c, y0)]
    d.line(pts, fill=color, width=int(round(t)), joint="curve")
    for i in range(4):
        px = x0 + c + (i + 0.3) * (w - c - t) / 4.4
        d.rectangle([px, y0 + h * 0.12, px + w * 0.08, y0 + h * 0.3], fill=color)


def render(W, H, lines, ready, ss=4):
    w, h = W * ss, H * ss
    u = min(w, h)
    im = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(im)
    margin = 0.07 * u
    avail = w - 2 * margin

    # sizes relative to the short side, shrunk together if a line is too wide
    k = 1.0
    while True:
        f_t = font("Roboto-Medium.ttf", 0.060 * u * k)
        f_d = font("Roboto-Regular.ttf", 0.044 * u * k)
        widest = max(max(f_t.getlength(a), f_d.getlength(b)) for a, b in lines)
        if widest <= avail or k < 0.5:
            break
        k *= 0.95

    # icons on top: SD card and a crossed-out power symbol (green tick when done)
    icon_h = 0.13 * u
    icon_y = margin + icon_h / 2
    sd_icon(d, w / 2 - icon_h * 0.75, icon_y, icon_h, WHITE)
    if ready:
        t = icon_h * 0.12
        x, y = w / 2 + icon_h * 0.75, icon_y
        s = icon_h * 0.4
        d.line([(x - s, y), (x - s * 0.25, y + s * 0.7), (x + s, y - s * 0.8)],
               fill=GREEN, width=int(round(t)), joint="curve")
    else:
        power_icon(d, w / 2 + icon_h * 0.75, icon_y + icon_h * 0.05, icon_h * 0.36, WHITE, True)

    # three blocks, spread over the space under the icons
    top = margin + icon_h + 0.06 * u
    bottom = h - margin
    block_h = cap_h(f_t) + 0.030 * u * k + cap_h(f_d) + 0.02 * u * k
    gap = (bottom - top - 3 * block_h) / 2
    gap = max(0.03 * u, min(gap, 0.09 * u))
    total = 3 * block_h + 2 * gap
    y = top + (bottom - top - total) / 2
    for title, detail in lines:
        yb = y + cap_h(f_t)
        d.text((w / 2, yb), title, font=f_t, fill=WHITE, anchor="ms")
        yb += 0.030 * u * k + cap_h(f_d) + 0.012 * u * k
        d.text((w / 2, yb), detail, font=f_d, fill=GREY, anchor="ms")
        y += block_h + gap

    return im.resize((W, H), Image.LANCZOS)


def ppm(im):
    return b"P6\n%d %d\n255\n" % im.size + im.tobytes()


def cpio_newc(files):
    """newc cpio (what the kernel's initramfs unpacker reads), regular files 0644."""
    out = io.BytesIO()

    def entry(ino, name, mode, data):
        nb = name.encode() + b"\0"
        hdr = "070701" + "".join("%08X" % v for v in (
            ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(nb), 0))
        out.write(hdr.encode() + nb)
        out.write(b"\0" * (-(110 + len(nb)) % 4))
        out.write(data)
        out.write(b"\0" * (-len(data) % 4))

    for i, (name, data) in enumerate(files, 1):
        entry(i, name, 0o100644, data)
    entry(0, "TRAILER!!!", 0, b"")
    return out.getvalue()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", "--width", type=int, default=640)
    p.add_argument("-H", "--height", type=int, default=480)
    p.add_argument("-o", "--out", required=True, help="gzip cpio to write")
    p.add_argument("--png-dir", help="also write PNG previews here")
    a = p.parse_args()

    files = []
    for name, lines in SCREENS.items():
        im = render(a.width, a.height, lines, ready=name.startswith("resized"))
        files.append((name, ppm(im)))
        if a.png_dir:
            os.makedirs(a.png_dir, exist_ok=True)
            im.save(os.path.join(a.png_dir, "%s-%dx%d.png" % (name[:-4], a.width, a.height)))
    with open(a.out, "wb") as f:
        # mtime 0: the same pictures give the same file
        f.write(gzip.compress(cpio_newc(files), 9, mtime=0))
    print("wrote %s (%dx%d)" % (a.out, a.width, a.height))


if __name__ == "__main__":
    main()
