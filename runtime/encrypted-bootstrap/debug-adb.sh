#!/system/bin/sh
export PATH=/system/bin:/vendor/bin
exec >/metadata/p3s-adb.log 2>&1
[ -d /data/misc/adb ] || exit 1
cp /odm/etc/p3s-runtime/adb_keys /data/misc/adb/adb_keys
chown 1000:2000 /data/misc/adb/adb_keys
chmod 640 /data/misc/adb/adb_keys
restorecon /data/misc/adb/adb_keys
setprop persist.sys.usb.config mtp,adb
setprop persist.sys.usb.adb.disabled 0
setprop sys.usb.config mtp,adb
setprop ctl.start adbd
settings put global development_settings_enabled 1
settings put global adb_enabled 1
echo authenticated_adb_enabled
