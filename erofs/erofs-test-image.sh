#!/bin/bash
# Make an EROFS test card from a release image zip: the same build, with system
# (and with --vendor also vendor) turned into EROFS. For a device test of the
# 4.19 staging erofs driver and a boot time / app start comparison against the
# ext4 release it was made from.
#
#   sudo erofs/erofs-test-image.sh lineage-18.1-...-r36s-android.img.zip [--vendor]
#
# Writes <name>-erofs.img.zip in the current directory. Nothing else changes:
# kernel, ramdisk and BOOT files are the release's. The kernel already has
# CONFIG_EROFS_FS=y + CONFIG_EROFS_FS_ZIP=y, and the ramdisk's fstab already has
# an erofs line for /system after the ext4 one (first stage init tries the next
# line with the same mount point when a mount fails). --vendor needs a ramdisk
# whose fstab has an erofs line for /vendor too; the script checks that.
set -euo pipefail

zip=${1:?usage: erofs-test-image.sh <release .img.zip> [--vendor]}
vendor=0
[ "${2:-}" = --vendor ] && vendor=1
here=$(cd "$(dirname "$0")" && pwd)
export PATH=$PATH:/sbin:/usr/sbin MTOOLS_SKIP_CHECK=1

# Sectors, as in mkimg.sh
BOOT_START=32768 BOOT_END=557055
SYS_START=1081344 SYS_END=5701008
VEN_START=557056 VEN_END=884735

[ "$(id -u)" = 0 ] || { echo "Must be root"; exit 1; }

# GNU dd with byte offsets, bs=512 takes many minutes for 2 GB
ddin() { # ddin <src> <dst> <start sector> <sectors>
    dd if="$1" of="$2" bs=1M iflag=skip_bytes,count_bytes skip=$(($3 * 512)) count=$(($4 * 512)) status=none
}
ddout() { # ddout <src> <image> <start sector>
    dd if="$1" of="$2" bs=1M oflag=seek_bytes seek=$(($3 * 512)) conv=notrunc status=none
}
for t in unzip zip mcopy cpio python3; do
    command -v "$t" >/dev/null || { echo "$t not found"; exit 1; }
done

name=$(unzip -Z1 "$zip" | grep '\.img$' | head -n1)
[ -n "$name" ] || { echo "No .img in $zip"; exit 1; }
out=$PWD/${name%.img}-erofs.img
[ -e "$out.zip" ] && { echo "$out.zip already exists"; exit 1; }

work=$(mktemp -d "${TMPDIR:-/tmp}/erofs-test.XXXXXX")
trap 'rm -rf "$work"' EXIT
unzip -q -d "$work" "$zip" "$name"
img=$work/$name

# The first-stage fstab lives in the ramdisk on BOOT
ddin "$img" "$work/boot.fat" $BOOT_START $((BOOT_END - BOOT_START + 1))
mcopy -i "$work/boot.fat" ::/ramdisk.uimg "$work/ramdisk.uimg"
tail -c +65 "$work/ramdisk.uimg" | gzip -dc | (cd "$work" && cpio -i --quiet fstab.rk30board 2>/dev/null) || true
fstab_has_erofs() {
    [ -f "$work/fstab.rk30board" ] &&
        grep -Eq "^[^#]*[[:space:]]$1[[:space:]]+erofs[[:space:]]" "$work/fstab.rk30board"
}
fstab_has_erofs /system || { echo "The ramdisk fstab has no erofs line for /system"; exit 1; }
if [ $vendor = 1 ] && ! fstab_has_erofs /vendor; then
    echo "The ramdisk fstab has no erofs line for /vendor (needs common night/o2-erofs)"
    exit 1
fi

# convert <name> <start> <end>: ext4 at <start> -> EROFS, rest of the partition zeroed
convert() {
    local part=$1 start=$2 sectors=$(($3 - $2 + 1))
    ddin "$img" "$work/$part.ext4" "$start" "$sectors"
    "$here/ext4-to-erofs.sh" "$work/$part.ext4" "$work/$part.erofs"
    rm -f "$work/$part.ext4"
    local size
    size=$(stat -c %s "$work/$part.erofs")
    [ "$size" -le $((sectors * 512)) ] || { echo "$part.erofs does not fit"; exit 1; }
    truncate -s $((sectors * 512)) "$work/$part.erofs"
    ddout "$work/$part.erofs" "$img" "$start"
    rm -f "$work/$part.erofs"
}
convert system $SYS_START $SYS_END
[ $vendor = 1 ] && convert vendor $VEN_START $VEN_END

mv "$img" "$out"
(cd "$(dirname "$out")" && zip -q "$(basename "$out").zip" "$(basename "$out")")
rm -f "$out"
echo "Wrote $out.zip"
