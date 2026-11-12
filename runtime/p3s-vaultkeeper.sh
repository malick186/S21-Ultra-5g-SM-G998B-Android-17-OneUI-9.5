#!/system/bin/sh
set -eu
export PATH=/system/bin:/vendor/bin
b=/data/adb/p3s-vk-compat
[ -f /metadata/p3s-vk-compat.enabled ] || exit 0
[ "$(getprop ro.product.vendor.model)" = SM-G998B ] || exit 0
exec > "$b/boot.log" 2>&1
[ "$(sha256sum /system/lib64/libvkmanager.so | cut -c1-64)" = 0fdf61d254ff10c50f9f5e9027e3d2f5e0ac1fb938637c086540f85ffb1596e4 ] || exit 0
[ "$(sha256sum "$b/libs/libvkmanager.so" | cut -c1-64)" = 4d84d6674aa779b3460ddcf94f69459ba828ed30ffe2d00feccc500245a81aa5 ]
[ "$(sha256sum "$b/libs/vendor.samsung.hardware.security.vaultkeeper@2.0.so" | cut -c1-64)" = adb95777c6db31a45ea88cb2b554e897c6e13c5802f4c4766e4fda89b35f1602 ]
/system/bin/nsenter -t 1 -m /system/bin/sh "$b/mount.sh"
echo "S21 stock VaultKeeper libraries mounted"
