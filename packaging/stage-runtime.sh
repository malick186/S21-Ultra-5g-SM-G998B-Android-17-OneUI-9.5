#!/sbin/sh
# Runs in recovery before dynamic partition writes, on freshly formatted storage.
set -eu
umask 077
cd /tmp/p3s-r6
sha256sum -c runtime.sha256
for volume in data metadata; do
    awk -v m="/$volume" '$2==m && $1 ~ /^\/dev\/block\// && $3 ~ /^(f2fs|ext4)$/ && $4 ~ /^rw,/ {ok=1} END {exit !ok}' /proc/mounts || { echo "Mount /$volume read-write in TWRP"; exit 1; }
done
[ ! -e /data/system/users/0 ] || { echo "Clean installation needs freshly formatted Data"; exit 1; }
[ ! -L /data/adb ]
if [ -e /data/adb ]; then
    [ -d /data/adb ] && [ -z "$(ls -A /data/adb)" ] || { echo "Existing root environment detected; exiting"; exit 1; }
fi
for flag in /metadata/p3s-ce-display.enabled /metadata/p3s-vk-compat.enabled; do
    [ ! -L "$flag" ] && { [ ! -e "$flag" ] || [ -f "$flag" ]; }
done
stage=$(mktemp -d /data/.p3s-r6.XXXXXX)
mkdir -p "$stage/post-fs-data.d" "$stage/service.d" "$stage/p3s-ce-display" "$stage/p3s-vk-compat/libs"
cp p3s-ce.sh p3s-vaultkeeper.sh "$stage/post-fs-data.d/"
cp p3s-display.sh "$stage/service.d/"
cp services.jar "$stage/p3s-ce-display/"
cp mount.sh "$stage/p3s-vk-compat/"
cp *.so "$stage/p3s-vk-compat/libs/"
chown -R 0:0 "$stage"
chcon -R u:object_r:adb_data_file:s0 "$stage"
chmod 755 "$stage/post-fs-data.d" "$stage/service.d" "$stage/p3s-vk-compat/libs"
chmod 700 "$stage/post-fs-data.d/"*.sh "$stage/service.d/"*.sh "$stage/p3s-vk-compat/mount.sh"
chmod 644 "$stage/p3s-ce-display/services.jar" "$stage/p3s-vk-compat/libs/"*.so
chcon u:object_r:system_file:s0 "$stage/p3s-ce-display/services.jar"
chcon -R u:object_r:system_lib_file:s0 "$stage/p3s-vk-compat/libs"
if [ -d /data/adb ]; then rmdir /data/adb; fi
mv "$stage" /data/adb
for flag in /metadata/p3s-ce-display.enabled /metadata/p3s-vk-compat.enabled; do
    touch "$flag"
    chmod 600 "$flag"
    chcon u:object_r:metadata_file:s0 "$flag"
done
sync