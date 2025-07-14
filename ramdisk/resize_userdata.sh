#!/system/bin/sh

if [ -f "/data/resize_done" ]; then
    echo "resize_userdata: Already resized, exiting" > /dev/kmsg
    exit 0
fi

echo "resize_userdata: Starting resize" > /dev/kmsg

# Unmount /data just in case (should be already mounted though)
umount /data

# Resize
resize2fs /dev/mmcblk0p3

# Remount /data
mount /data

# Create marker
touch "/data/resize_done"

echo "resize_userdata: Done resizing" > /dev/kmsg
exit 0
