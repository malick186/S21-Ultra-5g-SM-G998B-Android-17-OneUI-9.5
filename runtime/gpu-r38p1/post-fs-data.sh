#!/system/bin/sh
MODDIR=${0%/*}
exec > "$MODDIR/boot.log" 2>&1
[ "$(getprop ro.product.vendor.device)" = p3s ] || exit 0
[ -f "$MODDIR/disable" ] && exit 0
if [ -f "$MODDIR/trial-started" ] && [ ! -f "$MODDIR/verified" ]; then
 echo "Unverified trial: original driver retained on this boot"
 exit 0
fi
touch "$MODDIR/trial-started"
/system/bin/nsenter -t 1 -m /system/bin/sh "$MODDIR/mount.sh" "$MODDIR"
