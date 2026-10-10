#!/bin/bash
# Convert an Android ext4 image (raw or sparse) into an EROFS image that the
# 4.19 kernel's staging erofs driver can mount.
#
#   sudo erofs/ext4-to-erofs.sh system.img system.erofs
#
# Owner, group, mode, SELinux labels and file capabilities are copied from the
# ext4 image as they are. Needs root (debugfs rdump only keeps owners as root),
# debugfs (e2fsprogs), simg2img for sparse input, python3 and mkfs.erofs +
# fsck.erofs from erofs-utils 1.8 or newer (MKFS_EROFS / FSCK_EROFS to point at
# them). 1.7.1 (Ubuntu 24.04's package) writes broken small files from a tar
# when compression is on: fsck.erofs finds them, so the script stops.
#
# Format choices, all forced by the staging driver in kernel 4.19:
#  -Elegacy-compress  no compacted indexes and no lz4 0padding. The driver
#                     rejects any incompat feature bit (EROFS_ALL_REQUIREMENTS 0)
#  -C4096 (default)   4 KB physical clusters, CONFIG_EROFS_FS_CLUSTER_PAGE_LIMIT=1
#  lz4hc level 9      same decompression cost as lz4, 5% smaller than lz4;
#                     level 12 saves only 1 MB more and takes 2.6x as long
# Set EROFS_COMPRESS="" for an uncompressed image.
set -euo pipefail

src=${1:?usage: ext4-to-erofs.sh <ext4 image> <erofs out>}
out=${2:?usage: ext4-to-erofs.sh <ext4 image> <erofs out>}
here=$(cd "$(dirname "$0")" && pwd)
compress=${EROFS_COMPRESS--zlz4hc,9 -Elegacy-compress}
mkfs=${MKFS_EROFS:-mkfs.erofs}
fsck=${FSCK_EROFS:-fsck.erofs}
export PATH=$PATH:/sbin:/usr/sbin

[ "$(id -u)" = 0 ] || { echo "Must be root (debugfs rdump keeps owners only as root)"; exit 1; }
for t in debugfs "$mkfs" "$fsck" python3; do
    command -v "$t" >/dev/null || { echo "$t not found"; exit 1; }
done

work=$(mktemp -d "${TMPDIR:-/tmp}/ext4-to-erofs.XXXXXX")
trap 'rm -rf "$work"' EXIT

img=$src
if file "$src" | grep -qi "Android sparse image"; then
    simg2img "$src" "$work/raw.img"
    img=$work/raw.img
fi

mkdir "$work/tree"
debugfs -R "rdump / $work/tree" "$img" >/dev/null 2>&1
rmdir "$work/tree/lost+found" 2>/dev/null || true

# One ea_list per path, relative to the image root
(cd "$work/tree" && find .) | sed -e 's#^\./#/#' -e 's#^\.$#/#' -e 's#^#ea_list #' > "$work/cmds"
debugfs -f "$work/cmds" "$img" > "$work/ea.txt" 2>/dev/null

# The volume label of the ext4 image, if any, is kept
label=$(debugfs -R stats "$img" 2>/dev/null | sed -n 's/^Filesystem volume name: *//p')
[ "$label" = "<none>" ] && label=

# shellcheck disable=SC2086 # $compress is a list of options
python3 "$here/ext4tar.py" "$work/tree" "$work/ea.txt" |
    "$mkfs" --quiet -T0 ${label:+-L "$label"} $compress --tar=f "$out"

"$fsck" "$out" >/dev/null || { echo "fsck.erofs: $out is broken"; exit 1; }
echo "$out: $(($(stat -c %s "$out") / 1048576)) MiB (ext4 image: $(($(stat -c %s "$img") / 1048576)) MiB)"
