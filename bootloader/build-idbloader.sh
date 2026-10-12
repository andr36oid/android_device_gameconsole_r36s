#!/bin/bash
# Builds idbloader.img in this folder from Rockchip's rkbin: DDR init v2.12 and miniloader v1.40.
# The DDR init finds the RAM layout itself, so it also starts the clones with two RAM chips that
# the Hardkernel idbloader (DDR init v1.10 from 2018) leaves blinking red. Its debug UART is moved
# to UART2 M1 at 115200 like the rest of the boot chain: rkbin's default M0 is the SD card's data pins.
# trust.img stays the Hardkernel one from build-uboot.sh: rkbin's BL31 v1.37 doesn't start with this U-Boot.
# Needs git, python3 and mkimage (u-boot-tools).
# Usage: bootloader/build-idbloader.sh [empty work dir]
set -euo pipefail
REPO=https://github.com/rockchip-linux/rkbin
COMMIT=3e288fe814e059dd06833495f845cab04ac20a5c
DDR=bin/rk33/rk3326_ddr_333MHz_v2.12.bin
LOADER=bin/rk33/rk3326_miniloader_v1.40.bin
OUT=$(cd "$(dirname "$0")" && pwd)
WORK=${1:-$(mktemp -d)}
git clone -q --filter=blob:none --no-checkout "$REPO" "$WORK/rkbin"
git -C "$WORK/rkbin" checkout -q "$COMMIT" -- "$DDR" "$LOADER" tools/ddrbin_tool.py
cd "$WORK/rkbin"
sha256sum -c - <<SUMS
285a87e760a3586953f637b6de0fe80745b0ecf455dfb052bc3ecfc8b756cb7e  $DDR
473aacd5378f356757a71efeb54f4339925db154fbce288df7e3c1177f45bc28  $LOADER
SUMS
cp "$DDR" ddr.bin
python3 tools/ddrbin_tool.py rk3326 -g param.txt ddr.bin >/dev/null
sed -i -e 's/^uart iomux=.*/uart iomux=1/' -e 's/^uart baudrate=.*/uart baudrate=115200/' param.txt
python3 tools/ddrbin_tool.py rk3326 param.txt ddr.bin >/dev/null
mkimage -n px30 -T rksd -d ddr.bin "$OUT/idbloader.img" >/dev/null
cat "$LOADER" >> "$OUT/idbloader.img"
(cd "$OUT" && sha256sum idbloader.img)
