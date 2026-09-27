#!/bin/bash
set -euo pipefail

LINEAGEVERSION=lineage-18.1
DATE=$(date -u +%Y%m%d)
TIME=$(date -u +%H%M)
DEVICE=r36s-android
IMGNAME=$LINEAGEVERSION-$DATE-$TIME-$DEVICE.img
IMGSIZE=3    # GiB
OUTDIR=${ANDROID_PRODUCT_OUT:="../../../out/target/product/r36s"}
TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

if [ "$(id -u)" != 0 ]; then
    echo "Must be root to run script!"
    exit 1
fi

if [ -f "$IMGNAME" ]; then
    echo "File $IMGNAME already exists!"
    exit 1
fi

echo "Copying over kernel files"
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/Image" BOOT/ || true
cp ../common/resizing/prebuilt/Image-resizing BOOT/ || true
cp ./Image-recovery BOOT/ || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel0.dtb" BOOT/Panels/Panel0/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel1.dtb" BOOT/Panels/Panel1/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel2.dtb" BOOT/Panels/Panel2/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel3.dtb" BOOT/Panels/Panel3/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel4.dtb" BOOT/Panels/Panel4/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel5.dtb" BOOT/Panels/Panel5/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel6.dtb" BOOT/Panels/Panel6/rk3326-r36s-android.dtb || true
cp "$OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE-panel4.dtb" BOOT/rk3326-r36s-android.dtb || true

echo "Creating image file $IMGNAME..."
truncate -s "${IMGSIZE}G" "$IMGNAME"
sync

# The first-boot resizer (Image-resizing) runs "parted mkpart" for userdata and
# EASYROMS after 5701009s, and parted gives them the lowest free numbers. So
# numbers 6 and 7 are held by placeholders while vendor, metadata, misc and
# cache are created, and freed again, to keep userdata p6 and EASYROMS p7.
# The old BOOT partition's second half is where vendor and the rest now live.
echo "Creating partitions (GPT) on $IMGNAME..."
parted -s "$IMGNAME" mktable gpt
parted -s "$IMGNAME" mkpart BOOT fat32 32768s 557055s
parted -s "$IMGNAME" mkpart system ext4 1081344s 5701008s
parted -s "$IMGNAME" mkpart idbloader 64s 16383s
parted -s "$IMGNAME" mkpart uboot 16384s 24575s
parted -s "$IMGNAME" mkpart trust 24576s 32767s
parted -s "$IMGNAME" mkpart placeholder6 5701009s 5701016s
parted -s "$IMGNAME" mkpart placeholder7 5701017s 5701024s
parted -s "$IMGNAME" mkpart vendor ext4 557056s 884735s
parted -s "$IMGNAME" mkpart metadata ext4 884736s 917503s
parted -s "$IMGNAME" mkpart misc 917504s 925695s
parted -s "$IMGNAME" mkpart cache ext4 925696s 1081343s
parted -s "$IMGNAME" rm 7
parted -s "$IMGNAME" rm 6

dd if=bootloader/idbloader.img of="$IMGNAME" conv=fsync,notrunc bs=512 seek=64
dd if=bootloader/uboot.img of="$IMGNAME" conv=fsync,notrunc bs=512 seek=16384
dd if=bootloader/trust.img of="$IMGNAME" conv=fsync,notrunc bs=512 seek=24576

echo "Partition table:"
parted -s "$IMGNAME" unit s print
sync

p1_start=$(parted -s "$IMGNAME" unit s print | awk '/^ *1[[:space:]]/{gsub(/s/,"",$2); print $2}')
p1_end=$(parted -s "$IMGNAME" unit s print | awk '/^ *1[[:space:]]/{gsub(/s/,"",$3); print $3}')
p2_start=$(parted -s "$IMGNAME" unit s print | awk '/^ *2[[:space:]]/{gsub(/s/,"",$2); print $2}')
p2_end=$(parted -s "$IMGNAME" unit s print | awk '/^ *2[[:space:]]/{gsub(/s/,"",$3); print $3}')

if [ -z "$p1_start" ] || [ -z "$p2_start" ]; then
    echo "Failed to read partition start sectors."
    exit 1
fi

p1_sectors=$((p1_end - p1_start + 1))
p2_sectors=$((p2_end - p2_start + 1))

echo "p1 start: $p1_start sectors ($p1_sectors), p2 start: $p2_start sectors ($p2_sectors)"

BOOT_IMG="$TMPDIR/boot.img"
echo "Creating BOOT filesystem image ($p1_sectors sectors)..."
dd if=/dev/zero of="$BOOT_IMG" bs=512 count="$p1_sectors" status=none

if command -v mkfs.fat >/dev/null 2>&1; then
    MKFS_FAT=mkfs.fat
elif command -v mkfs.vfat >/dev/null 2>&1; then
    MKFS_FAT=mkfs.vfat
elif command -v mkdosfs >/dev/null 2>&1; then
    MKFS_FAT=mkdosfs
else
    echo "No FAT mkfs tool found (mkfs.fat|mkfs.vfat|mkdosfs)."
    exit 1
fi
$MKFS_FAT -F 32 -n BOOT "$BOOT_IMG"

BOOT_TMP="$TMPDIR/BOOT_COPY"
mkdir -p "$BOOT_TMP"
cp -a BOOT/* "$BOOT_TMP"/ || true

# First-stage ramdisk. This U-Boot only takes legacy uImage ramdisks, so it is
# wrapped with mkimage. ramdisk.uimg has Magisk baked in; ramdisk-stock.uimg is
# the plain one, rename it to ramdisk.uimg if Magisk ever breaks the boot.
RAMDISK_SRC="$OUTDIR/ramdisk.img"
if [ ! -f "$RAMDISK_SRC" ]; then
    echo "Ramdisk not found at $RAMDISK_SRC (mka bootimage builds it)"
    exit 1
fi
# u-boot-tools if installed, else the one the Lineage tree ships
MKIMAGE=$(command -v mkimage || echo ../../../prebuilts/tools-lineage/linux-x86/bin/mkimage)
if [ ! -x "$MKIMAGE" ]; then
    echo "mkimage not found. Install u-boot-tools."
    exit 1
fi
"$MKIMAGE" -A arm64 -O linux -T ramdisk -C none -n "andr36oid stock ramdisk" \
    -d "$RAMDISK_SRC" "$BOOT_TMP/ramdisk-stock.uimg" >/dev/null
MAGISK_APK=../common/magisk/Magisk.apk
if [ -f "$MAGISK_APK" ] && [ "$(head -c 2 "$MAGISK_APK")" = "PK" ]; then
    bash ../common/magisk/inject_magisk.sh --ramdisk "$RAMDISK_SRC" \
        --apk "$MAGISK_APK" --out "$TMPDIR/ramdisk-magisk.cpio.gz"
    "$MKIMAGE" -A arm64 -O linux -T ramdisk -C none -n "andr36oid ramdisk (Magisk)" \
        -d "$TMPDIR/ramdisk-magisk.cpio.gz" "$BOOT_TMP/ramdisk.uimg" >/dev/null
else
    echo "No Magisk APK (or only an LFS pointer), the ramdisk has no root"
    cp "$BOOT_TMP/ramdisk-stock.uimg" "$BOOT_TMP/ramdisk.uimg"
fi
# Boot logos with the build's version, the committed ones stay as a fallback
VERSION=$(sed -n 's/^ro.andr36oid.version=//p' "$OUTDIR/system/product/build.prop" 2>/dev/null || true)
if python3 -c 'import PIL' 2>/dev/null; then
    echo "Drawing boot logos for ${VERSION:-an unknown version}"
    python3 BOOT/gen-logo.py --build "$VERSION" -o "$BOOT_TMP/logo.bmp"
    python3 BOOT/gen-logo.py --build "$VERSION" -w 720 -H 720 -o "$BOOT_TMP/Panels/Plus/logo.bmp"
else
    echo "Pillow not found, keeping the committed boot logos"
fi
# U-Boot shows logo_kernel.bmp while starting the kernel and hands it over, so the
# screen stays on the logo until Android draws instead of going blank
cp "$BOOT_TMP/logo.bmp" "$BOOT_TMP/logo_kernel.bmp"
cp "$BOOT_TMP/Panels/Plus/logo.bmp" "$BOOT_TMP/Panels/Plus/logo_kernel.bmp"
# The generator isn't needed on the card
rm -rf "$BOOT_TMP/gen-logo.py" "$BOOT_TMP/fonts"
if [ -f "$BOOT_TMP/uboot-dtb" ]; then
    mv "$BOOT_TMP/uboot-dtb" "$BOOT_TMP/rg351mp-kernel.dtb"
fi

if ! command -v mcopy >/dev/null 2>&1; then
    echo "mtools (mcopy) not found. Install mtools."
    exit 1
fi
export MTOOLS_SKIP_CHECK=1

# copy files one-by-one to avoid trying to create '.' or '..' entries
cd "$BOOT_TMP"
shopt -s dotglob nullglob
for f in * .*; do
    [ "$f" = "." ] && continue
    [ "$f" = ".." ] && continue
    # if it's a directory, mcopy -s will copy recursively
    mcopy -s -i "$BOOT_IMG" "$f" ::/ || {
        # fallback: create directory then copy contents
        if [ -d "$f" ]; then
            mmd -i "$BOOT_IMG" ::/"$f" || true
            (cd "$f" && for sub in * .*; do
                [ "$sub" = "." ] && continue
                [ "$sub" = ".." ] && continue
                mcopy -s -i "$BOOT_IMG" "$f/$sub" ::/"$f"/ || true
            done)
        fi
    }
done
cd - >/dev/null

echo "Embedding BOOT filesystem into $IMGNAME at sector $p1_start..."
dd if="$BOOT_IMG" of="$IMGNAME" bs=512 seek="$p1_start" conv=notrunc,fsync status=none

echo "Copying system image into partition 2..."
SYS_SRC="$OUTDIR/system.img"
SYS_RAW="$TMPDIR/system.raw.img"

if [ ! -f "$SYS_SRC" ]; then
    echo "System image not found at $SYS_SRC"
    exit 1
fi

if file "$SYS_SRC" | grep -qi "Android sparse image"; then
    if command -v simg2img >/dev/null 2>&1; then
        simg2img "$SYS_SRC" "$SYS_RAW"
        dd if="$SYS_RAW" of="$IMGNAME" bs=512 seek="$p2_start" conv=notrunc,fsync status=none
    else
        echo "System image is Android sparse and simg2img is not installed."
        exit 1
    fi
else
    dd if="$SYS_SRC" of="$IMGNAME" bs=512 seek="$p2_start" conv=notrunc,fsync status=none
fi

echo "Copying vendor image into the vendor partition..."
VENDOR_SRC="$OUTDIR/vendor.img"
VENDOR_RAW="$TMPDIR/vendor.raw.img"
if [ ! -f "$VENDOR_SRC" ]; then
    echo "Vendor image not found at $VENDOR_SRC (mka vendorimage builds it)"
    exit 1
fi
if file "$VENDOR_SRC" | grep -qi "Android sparse image"; then
    simg2img "$VENDOR_SRC" "$VENDOR_RAW"
else
    cp "$VENDOR_SRC" "$VENDOR_RAW"
fi
if [ "$(stat -c %s "$VENDOR_RAW")" -gt $(((884735 - 557056 + 1) * 512)) ]; then
    echo "vendor.img is larger than the vendor partition"
    exit 1
fi
dd if="$VENDOR_RAW" of="$IMGNAME" bs=512 seek=557056 conv=notrunc,fsync status=none

# metadata and cache get an empty ext4 here, so Magisk finds /metadata on the
# very first boot. Android's own mke2fs, the host one may enable ext4 features
# the 4.19 kernel does not know.
HOSTBIN=${ANDROID_HOST_OUT:-../../../out/host/linux-x86}/bin
mkfs_part() { # mkfs_part <label> <start sector> <end sector>
    local img="$TMPDIR/$1.img"
    truncate -s $((($3 - $2 + 1) * 512)) "$img"
    MKE2FS_CONFIG="$HOSTBIN/mke2fs.conf" "$HOSTBIN/mke2fs" -q -t ext4 -F -b 4096 -L "$1" "$img"
    dd if="$img" of="$IMGNAME" bs=512 seek="$2" conv=notrunc,fsync status=none
    rm -f "$img"
}
mkfs_part metadata 884736 917503
mkfs_part cache 925696 1081343

sync
parted -s "$IMGNAME" unit s print

echo "Done, created $IMGNAME!"
rm -rf "$BOOT_IMG" "$BOOT_TMP" "$SYS_RAW" "$VENDOR_RAW"
zip -r -q "$IMGNAME.zip" "$IMGNAME"
echo "Packaged $IMGNAME.zip"
