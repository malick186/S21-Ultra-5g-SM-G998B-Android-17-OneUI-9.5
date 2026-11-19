#!/system/bin/sh
set -eu
export PATH=/system/bin:/vendor/bin
src=/odm/etc/p3s-runtime
exec >/metadata/p3s-bootstrap.log 2>&1
# init.usb.rc must create /data/adb with encryption=Require first.
# Never mkdir /data/adb here, nor populate it from recovery.
[ -d /data/adb ] && [ ! -L /data/adb ] || { log -t P3sBootstrap "Encrypted adb directory not ready"; exit 1; }
cd "$src"
sha256sum -c payload.sha256 || exit 1
mkdir -p /data/adb/post-fs-data.d /data/adb/service.d /data/adb/p3s-vk-compat/libs
for n in p3s-ce.sh p3s-vaultkeeper.sh; do cp "$src/$n" /data/adb/post-fs-data.d/; done
cp "$src/p3s-display.sh" /data/adb/service.d/
cp "$src/mount.sh" /data/adb/p3s-vk-compat/
cp "$src/"*.so /data/adb/p3s-vk-compat/libs/
chown -R 0:0 /data/adb/post-fs-data.d /data/adb/service.d /data/adb/p3s-vk-compat
chmod 755 /data/adb/post-fs-data.d /data/adb/service.d /data/adb/p3s-vk-compat /data/adb/p3s-vk-compat/libs
chmod 700 /data/adb/post-fs-data.d/p3s-ce.sh /data/adb/post-fs-data.d/p3s-vaultkeeper.sh /data/adb/service.d/p3s-display.sh /data/adb/p3s-vk-compat/mount.sh
chmod 644 /data/adb/p3s-vk-compat/libs/*.so
chcon -R u:object_r:adb_data_file:s0 /data/adb/post-fs-data.d /data/adb/service.d /data/adb/p3s-vk-compat
chcon -R u:object_r:system_lib_file:s0 /data/adb/p3s-vk-compat/libs
if [ ! -f /data/adb/p3s-vk-compat/.initialized ]; then
    touch /metadata/p3s-ce-display.enabled /metadata/p3s-vk-compat.enabled
    chmod 600 /metadata/p3s-ce-display.enabled /metadata/p3s-vk-compat.enabled
    chcon u:object_r:metadata_file:s0 /metadata/p3s-ce-display.enabled /metadata/p3s-vk-compat.enabled
    touch /data/adb/p3s-vk-compat/.initialized
fi
log -t P3sBootstrap "Runtime staged after encrypted directory creation"
exec /system/bin/sh /data/adb/post-fs-data.d/p3s-ce.sh
