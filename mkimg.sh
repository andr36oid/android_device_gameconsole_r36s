#/bin/bash

LINEAGEVERSION=lineage-18.1
DATE=`date -u +%Y%m%d`
DEVICE=r36s-android
IMGNAME=$LINEAGEVERSION-$DATE-$DEVICE.img
IMGSIZE=3
OUTDIR=${ANDROID_PRODUCT_OUT:="../../../out/target/product/r36s"}

if [ `id -u` != 0 ]; then
	echo "Must be root to run script!"
	exit
fi

if [ -f $IMGNAME ]; then
	echo "File $IMGNAME already exists!"
else
    echo "Copying over kernel files"
    cp $OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/Image BOOT/
	cp ../common/resizing/prebuilt/Image-resizing BOOT/
    cp $OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE.dtb BOOT/
    cp $OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE.dtb BOOT/rk3326-rg351mplus.dtb
	echo "Creating image file $IMGNAME..."
	dd if=/dev/zero of=$IMGNAME bs=1M count=$(echo "$IMGSIZE*1024" | bc)
	sync
	echo "Creating partitions..."
	# Make the disk MBR type (msdos)
	parted $IMGNAME mktable msdos

	# Copy u-boot data (skip the first sector because it is MBR data)
	dd if=uboot.img of=$IMGNAME bs=512 skip=1 seek=1 count=32767 conv=notrunc
	# Making BOOT partitions (size 1081344 sector - 32768 sector = 1048576  sectors * 512 = 512MiB)
	parted -s $IMGNAME mkpart primary fat32 32768s 1081343s
    # Set boot flag
    parted -s $IMGNAME set 1 boot on
	# Making rootfs partitions (size 1Gi)
	parted -s $IMGNAME mkpart primary ext4 1081344s 5701008s
	parted -s $IMGNAME mkpart primary ext4 5701009s 100%
	# Verify
	parted $IMGNAME print
	sync
	LOOPDEV=`kpartx -av $IMGNAME | awk 'NR==1{ sub(/p[0-9]$/, "", $3); print $3 }'`
	sync
	if [ -z "$LOOPDEV" ]; then
		echo "Unable to find loop device!"
		kpartx -d $IMGNAME
		exit
	fi
	echo "Image mounted as $LOOPDEV"
	sleep 5
	mkfs.fat -F 32 /dev/mapper/${LOOPDEV}p1 -n BOOT
	mkfs.ext4 /dev/mapper/${LOOPDEV}p2 -L system
	mkfs.ext4 /dev/mapper/${LOOPDEV}p3 -L userdata
	echo "Copying system..."
	dd if=$OUTDIR/system.img of=/dev/mapper/${LOOPDEV}p2 bs=1M
	#echo "Copying vendor..."
	#dd if=$OUTDIR/vendor.img of=/dev/mapper/${LOOPDEV}p3 bs=1M
	echo "Copying BOOT..."
	mkdir -p sdcard/BOOT
	sync
	mount /dev/mapper/${LOOPDEV}p1 sdcard/BOOT
	sync
	cp -R BOOT/* sdcard/BOOT
    mv sdcard/BOOT/uboot-dtb sdcard/BOOT/rg351mp-kernel.dtb
	sync
	umount /dev/mapper/${LOOPDEV}p1
	rm -rf sdcard
	kpartx -d $IMGNAME
	sync
	echo "Done, created $IMGNAME!"
    echo "Cleanup..."
    rm BOOT/Image*
    rm BOOT/*.dtb
	dd if=uboot.img of=$IMGNAME bs=512 skip=1 seek=1 count=32767 conv=notrunc
	parted -s $IMGNAME mkpart primary ext2 0% 32767s
	parted -s $IMGNAME rm 3
fi
