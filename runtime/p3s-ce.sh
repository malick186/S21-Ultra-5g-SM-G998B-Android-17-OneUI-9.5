#!/system/bin/sh
set -eu
export PATH=/system/bin:/vendor/bin
if ! /system/bin/sh /data/adb/post-fs-data.d/p3s-vaultkeeper.sh; then log -t P3sVaultKeeper "Mount failed; continuing framework startup"; fi
base=/data/adb/p3s-ce-display
[ -f /metadata/p3s-ce-display.enabled ] || exit 0
[ "$(getprop ro.product.vendor.model)" = SM-G998B ] || exit 0
[ "$(sha256sum /system/framework/services.jar | cut -c1-64)" = 924f73f99767c848d6dff9e7802dc7c29e96c4303fb1980acb46646a49721ff6 ] || exit 0
[ "$(sha256sum "$base/services.jar" | cut -c1-64)" = 4a9bf7ad445ee7389c3953ed416606ba9cdc7d6bf6ee4f38f871004fe0e578d2 ] || exit 1
nsenter -t 1 -m -- /system/bin/mount -o bind,ro "$base/services.jar" /system/framework/services.jar
