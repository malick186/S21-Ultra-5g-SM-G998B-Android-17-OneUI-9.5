#!/bin/bash
set -eo pipefail
cd /opt/codex-rom/monsterrom-p3s/source
source ./buildenv.sh p3s
export P3S_VINTF_TOOLS_DIR=/opt/codex-rom/monsterrom-p3s/vintf-host/otatools-16644040
export ROM_PACKAGE_DIR=/mnt/d/Codex-ROM/p3s/releases/a17-r2
mkdir -p "$ROM_PACKAGE_DIR"
TARGET="$ROM_PACKAGE_DIR/p3s_A17_VINTF_r2-target_files.zip"
INSTALLER="$ROM_PACKAGE_DIR/MonsterROM_A17_p3s_SM-G998B_r2_TEST.zip"
[ ! -e "$TARGET" ] && [ ! -e "$INSTALLER" ] || { echo 'Existing artifacts retained; refusing overwrite'; exit 1; }
# The fully built APK/system tree is retained. Only the verified boot cohort and
# an additive original-target VINTF fragment changed. Do not fabricate the
# make_rom completion marker or suppress any final checks.
bash "$SRC_DIR/platform/exynos2100/patches/floppy/customize.sh" verify
python3 "$SRC_DIR/scripts/internal/check_p3s_boot_metadata.py" "$WORK_DIR/kernel/boot.img" "$WORK_DIR/system/system/build.prop"
python3 "$SRC_DIR/scripts/internal/check_p3s_image_metadata.py" "$WORK_DIR" "$OUT_DIR/target/p3s/policy-check/file-context-labels.txt"
python3 "$SRC_DIR/scripts/internal/check_p3s_policy.py" "$WORK_DIR" "$TOOLS_DIR/bin/secilc" "$OUT_DIR/target/p3s/policy-check"
python3 "$SRC_DIR/scripts/internal/check_p3s_policy_access.py" "$WORK_DIR" "$OUT_DIR/target/p3s/policy-check"
python3 "$SRC_DIR/scripts/internal/check_p3s_vintf.py" "$WORK_DIR" "$OUT_DIR/target/p3s/vintf-check"
"$SRC_DIR/scripts/internal/create_target_files_zip.sh" "$TARGET"
bash "$SRC_DIR/platform/exynos2100/patches/floppy/customize.sh" verify --zip "$TARGET"
"$SRC_DIR/scripts/build_flashable_zip.sh" -o "$INSTALLER" "$TARGET"
echo 'A17_R2_RELEASE_BUILD_COMPLETE'
