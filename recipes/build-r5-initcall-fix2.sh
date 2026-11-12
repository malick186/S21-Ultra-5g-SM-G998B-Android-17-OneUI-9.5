#!/bin/bash
set -euo pipefail
base=/opt/codex-rom/monsterrom-p3s
cd "$base/kernel-source"
export PATH="/opt/codex-kernel/p3s-v7/toolchain/clang-r596125/bin:$PWD/build/bin:$PATH"
export KBUILD_BUILD_USER=unica KBUILD_BUILD_HOST=kernel-builder KBUILD_BUILD_VERSION=1
export KBUILD_BUILD_TIMESTAMP='Mon Oct 26 19:53:18 UTC 2026'
export PLATFORM_VERSION=12 ANDROID_MAJOR_VERSION=s TARGET_SOC=universal2100
export SKIP_FIPS_CRYPTO_INTEGRITY=1 SKIP_EXYNOS_FMP_INTEGRITY=1
make -j2 O=out CC=clang LD=ld.lld LLVM=1 LLVM_IAS=1 ARCH=arm64 USE_THINLTO_CACHE=0 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- Image modules > "$base/records/beta2-r5-kernel-fix2/build.log" 2>&1
echo R5_TARGETED_KERNEL_BUILD_COMPLETE

