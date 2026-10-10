#!/bin/bash
# Builds idbloader.img, uboot.img and trust.img in this folder from source:
# github.com/andr36oid/u-boot (Hardkernel ODROID-GO Advance U-Boot, R36S fork by sonic011gamer).
# It loads its screen DTB from BOOT as rg351mp/rg351p/rg351v-uboot.dtb, picked by the board id.
# Needs git, make, bc, python and an aarch64-linux-gnu cross compiler.
# Usage: bootloader/build-uboot.sh [empty work dir]
set -euo pipefail
REPO=https://github.com/andr36oid/u-boot
COMMIT=3fb6300df563210f752cd57e3b22714f39d3ef56
OUT=$(cd "$(dirname "$0")" && pwd)
WORK=${1:-$(mktemp -d)}
git clone -q "$REPO" "$WORK/u-boot"
git -C "$WORK/u-boot" checkout -q "$COMMIT"
# make.sh wants the Linaro 6.3.1 toolchain next to the tree: point it at the host cross compiler
TC=$WORK/prebuilts/gcc/linux-x86/aarch64/gcc-linaro-6.3.1-2017.05-x86_64_aarch64-linux-gnu/bin
mkdir -p "$TC"
for t in "$(dirname "$(command -v aarch64-linux-gnu-gcc)")"/aarch64-linux-gnu-*; do ln -sf "$t" "$TC/"; done
# Newer compilers warn where GCC 6 did not
(cd "$WORK/u-boot" && KCFLAGS="-Wno-error -fcommon" ./make.sh odroidgoa)
cp "$WORK/u-boot/sd_fuse/idbloader.img" "$WORK/u-boot/sd_fuse/uboot.img" "$WORK/u-boot/sd_fuse/trust.img" "$OUT/"
(cd "$OUT" && sha256sum idbloader.img uboot.img trust.img)
