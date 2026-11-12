set -eu
src=/opt/codex-rom/monsterrom-p3s/source
old=/opt/codex-rom/monsterrom-p3s/records/hardware-sample
stage=$(mktemp -d /opt/codex-rom/p3s-init.XXXXXX)
bin="$src/out/tools/bin"
export PATH="$bin:$PATH"
out="$PWD/outputs/monsterrom-p3s/display-persistence"
orig=/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/startup-records/odm-hardware-sample.img
cp -a "$old/input" "$stage/input"
cat >> "$stage/input/etc/init/p3s-startup.rc" <<'RC'

service p3s-ce-profile /system/bin/sh /data/adb/post-fs-data.d/p3s-ce.sh
    disabled
    oneshot
    user root
    group root
    seclabel u:r:ksu:s0

on post-fs-data
    exec_start p3s-ce-profile

service p3s-display-profile /system/bin/sh /data/adb/service.d/p3s-display.sh
    disabled
    oneshot
    user root
    group root
    seclabel u:r:ksu:s0

on property:sys.boot_completed=1
    start p3s-display-profile
RC
img="$stage/odm.img"
"$bin/mkfs.erofs" -zlz4hc,9 -T1640995200 --mount-point=/odm --file-contexts="$old/contexts" --fs-config-file="$old/fs_config" "$img" "$stage/input" > "$stage/build.log"
mkdir "$stage/original"
cp "$orig" "$stage/original/odm.img"
"$bin/avbtool" verify_image --image "$stage/original/odm.img" --key "$src/security/avb/testkey_rsa4096.pem"
"$bin/avbtool" add_hashtree_footer --image "$img" --partition_name odm --partition_size 548864 --hash_algorithm sha256 --salt 20c1f04b715a1195d07289207e1cc5e02a0abe662fd77ca992906421b3922ee2 --algorithm SHA256_RSA4096 --key "$src/security/avb/testkey_rsa4096.pem"
"$bin/avbtool" verify_image --image "$img" --key "$src/security/avb/testkey_rsa4096.pem"
mkdir "$stage/before" "$stage/after"
"$bin/fsck.erofs" --extract="$stage/before" "$orig"
"$bin/fsck.erofs" --extract="$stage/after" "$img"
diff -qr "$stage/before" "$stage/after" > "$stage/diff" || test "$?" = 1
test "$(wc -l < "$stage/diff")" = 1
grep -F 'p3s-startup.rc' "$stage/diff"
cp "$img" "$out/odm-ce-display.img"
sha256sum "$out/odm-ce-display.img"
