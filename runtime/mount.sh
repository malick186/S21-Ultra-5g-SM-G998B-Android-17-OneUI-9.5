set -eu
b=/data/adb/p3s-vk-compat
lower="$b/lower"
mkdir -p "$lower"
mount -t tmpfs -o size=2m,mode=0755 tmpfs "$lower"
cp "$b"/libs/*.so "$lower/"
chmod 644 "$lower"/*.so
chcon u:object_r:system_lib_file:s0 "$lower" "$lower"/*.so
mount -t overlay -o "ro,lowerdir=$lower:/system/lib64" overlay /system/lib64
