#!/system/bin/sh
set -eu
BASE=$1
while read -r OLD NEW DEST; do
 [ "$(sha256sum "$DEST" | cut -c1-64)" = "$OLD" ]
 [ "$(sha256sum "$BASE/payload$DEST" | cut -c1-64)" = "$NEW" ]
done < "$BASE/manifest.txt"
[ "${2:-}" = check ] && exit 0
MOUNTED=""
rollback() { for DEST in $MOUNTED; do umount "$DEST" || true; done; }
trap rollback EXIT
while read -r OLD NEW DEST; do
 case "$DEST" in
  *.so) chcon u:object_r:same_process_hal_file:s0 "$BASE/payload$DEST" ;;
  *.xml) chcon u:object_r:vendor_configs_file:s0 "$BASE/payload$DEST" ;;
 esac
 mount -o bind "$BASE/payload$DEST" "$DEST"
 MOUNTED="$DEST $MOUNTED"
 [ "$(sha256sum "$DEST" | cut -c1-64)" = "$NEW" ]
done < "$BASE/manifest.txt"
trap - EXIT
echo "All eight driver payload files mounted and verified"
