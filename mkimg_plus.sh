#/bin/bash

LINEAGEVERSION=lineage-18.1
DATE=`date -u +%Y%m%d`
TIME=`date -u +%H%M`
DEVICE=r36splus-android
IMGNAME=$LINEAGEVERSION-$DATE-$TIME-$DEVICE.img
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
	cp ./Image-recovery BOOT/
	cp $OUTDIR/obj/KERNEL_OBJ/arch/arm64/boot/dts/rockchip/rk3326-$DEVICE.dtb BOOT/rk3326-r36s-android.dtb
	echo "Creating image file $IMGNAME..."
	dd if=/dev/zero of=$IMGNAME bs=1M count=$(echo "$IMGSIZE*1024" | bc)
	sync
	echo "Creating partitions..."
	# Make the disk GPT
	parted -s $IMGNAME mktable gpt

	## Create the bootloader partitions and fuse them

	# Making BOOT partitions (size 1081344 sector - 32768 sector = 1048576  sectors * 512 = 512MiB), put it as 1st partition
	# otherwise it will not find the boot files (uboot skill issue?)
	parted -s $IMGNAME mkpart BOOT fat32 32768s 1081343s
    # Set boot flag
    #parted -s $IMGNAME set 1 boot on

	# Making rootfs partitions (size 1Gi)
	parted -s $IMGNAME mkpart system ext4 1081344s 5701008s

	# create bootloader partitions at last ( even though they're at the start)
	parted -s $IMGNAME mkpart idbloader 64s 16383s
	parted -s $IMGNAME mkpart uboot 16384s 24575s
	parted -s $IMGNAME mkpart trust 24576s 32767s
	sudo dd if=bootloader/idbloader.img of=$IMGNAME conv=fsync,notrunc bs=512 seek=64
	sudo dd if=bootloader/uboot.img of=$IMGNAME conv=fsync,notrunc bs=512 seek=16384
	sudo dd if=bootloader/trust.img of=$IMGNAME conv=fsync,notrunc bs=512 seek=24576
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

	echo "Copying system..."
	dd if=$OUTDIR/system.img of=/dev/mapper/${LOOPDEV}p2 bs=1M
	echo "Copying BOOT..."
	mkdir -p sdcard/BOOT
	sync
	mount /dev/mapper/${LOOPDEV}p1 sdcard/BOOT
	sync
	cp -R BOOT/* sdcard/BOOT
    cp sdcard/BOOT/Panels/Plus/rg351mp-kernel.dtb sdcard/BOOT/rg351mp-kernel.dtb
	cp sdcard/BOOT/Panels/Plus/logo.bmp sdcard/BOOT/logo.bmp
	sync
	umount /dev/mapper/${LOOPDEV}p1
	rm -rf sdcard
	kpartx -d $IMGNAME
	sync
	echo "Done, created $IMGNAME!"
    echo "Cleanup..."
    rm BOOT/Image*
    rm BOOT/*.dtb
	zip -r $IMGNAME.zip $IMGNAME
fi
