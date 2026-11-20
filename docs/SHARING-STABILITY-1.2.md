# Sharing Stability 1.2

GitHub carries the source, patches, build recipe, checksums and validation
notes. The Android firmware, proprietary apps, keys, device backups and
private test logs belong outside the repository and release assets. GitHub's
generated source archives are for source review and local builds.

The reference Stability 1.2 DEV LOCAL ZIP includes a tester's public ADB
key in ODM. The key was for one authorized development computer. Use the
key-free recipe below to prepare a separate local installer without that
authorization.

## Build the key-free local installer

The recipe takes your locally held, hash-matched Stability 1.2 DEV LOCAL ZIP
and the Linux MonsterROM build tree described in the [build guide](BUILD.md).
It needs Brotli, OpenSSL, the built Android host tools, and a Linux environment
with read-only EROFS loop mounts. Use a local output directory with space for
two installer-sized files.

```sh
python3 packaging/sanitize-stability12.py \
  --archive /inputs/MonsterROM-p3s-SM-G998B-Stability-1.2-DEV-LOCAL.zip \
  --source /work/MonsterROM \
  --output /releases/MonsterROM-p3s-SM-G998B-Stability-1.2-KEY-FREE-LOCAL.zip
```

The recipe removes the ODM ADB allowlist and its boot service and stops the
display profile from automatically enabling USB debugging. It preserves the
HD+, FHD+ and QHD+ profiles and the matching Night mode images. It checks
ODM content and file labels, all four decoded partition hashes and the
recovery signature. It writes the local ZIP, checksum and verification
record together.

The [clean-install test](STABILITY-1.2.md) applied to the DEV LOCAL
reference ZIP. The key-free build needs its own first-boot test. USB
debugging and host authorization are enabled interactively when needed.
The full installer still includes the firmware and apps needed by this
port. It remains a local artifact. The public recipe requires the pinned
local inputs and does not supply them.
