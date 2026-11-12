#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
dest=${1:?Usage: checkout-sources.sh NEW_DIRECTORY}
mkdir -p "$dest"
checkout() {
    local name=$1 url=$2 commit=$3
    test ! -e "$dest/$name" || { echo "$dest/$name exists" >&2; return 1; }
    git init -q "$dest/$name"
    git -C "$dest/$name" remote add origin "$url"
    git -C "$dest/$name" fetch --depth=1 origin "$commit"
    git -C "$dest/$name" checkout -q -b p3s-r6 FETCH_HEAD
    test "$(git -C "$dest/$name" rev-parse HEAD)" = "$commit"
    git -C "$dest/$name" apply --index "$root/patches/$name.patch"
}
checkout rom https://github.com/devcore94/MonsterROM.git 9353588dce5cd12baebbb0effa124372e45544cf
checkout kernel https://github.com/FlopKernel-Series/flop_exynos2100_kernel.git 113ce9d986f74e1526981324ec164e4d90930071
git -C "$dest/rom" submodule update --init --recursive
git -C "$dest/kernel" submodule update --init build/mkbootimg
echo "Source checkouts ready. See docs/BUILD.md for the required firmware and release inputs."
