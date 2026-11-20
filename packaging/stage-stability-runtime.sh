#!/sbin/sh
set -eu
for volume in data metadata; do
 awk -v m="/$volume" '$2==m && $1 ~ /^\/dev\/block\// && $3 ~ /^(f2fs|ext4)$/ && $4 ~ /^rw,/ {ok=1} END {exit !ok}' /proc/mounts || { echo "Mount /$volume read-write"; exit 1; }
done
[ ! -e /data/system/users/0 ] || { echo "Freshly formatted Data required"; exit 1; }
[ ! -e /data/adb ] || { echo "Do not prepopulate /data/adb before Android encryption setup"; exit 1; }
# No runtime files are written to Data or Metadata here. ODM bootstraps later.
