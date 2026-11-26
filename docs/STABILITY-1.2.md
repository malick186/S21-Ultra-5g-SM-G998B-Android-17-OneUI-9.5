# Stability 1.2 DEV LOCAL

The complete recovery installer passed a clean flash on one Exynos Galaxy S21 Ultra **SM-G998B** (`p3s`) on 20 November 2026. Setup Wizard reached One UI Home and both Android setup flags were set. Recovery reported a successful install and the four logical partition hashes, their physical storage readbacks, and the inherited boot image hashes all matched.

| Test | Result |
|---|---|
| HD+ | 720 × 1600 at 320 dpi. Display and composition bounds matched, both physical edges fit, and touch worked. |
| FHD+ | 1080 × 2400 at 480 dpi. Display and composition bounds matched, both physical edges fit, and touch worked. |
| QHD+ | 1440 × 3200 at 640 dpi. Display and composition bounds matched, both physical edges fit, and touch worked. |
| Night mode | Processed all 12 capture frames, completed denoising, and saved a 4000 × 3000 JPEG with `NO_ERROR`. The saved photo opened. |

All three modes were selected through Samsung Settings. HD+ was left active after the test. The Night-mode result covers the tested capture and lighting conditions.

## Included changes

- Use the active panel mode for framework display dimensions and apply a density proportional to each resolution. [Geometry patch](../patches/p3s-active-mode-geometry.patch) · [Resolution profile](../runtime/encrypted-bootstrap/shell-profile.sh)
- Restore the stock MPI wrapper and the MultiFrameProcessing30 SNAP wrapper from the pinned SM-G998B firmware. Use their matched Mali r38p0 graphics stack in the Stability build. This replaces the earlier r38p1 update for Stability 1.2 and preserves the [historical GPU experiment](POST-R7-UPDATES.md). [Camera source patch](../patches/p3s-camera-mpi.sh)
- Check fresh writable Data and Metadata before writing partitions, then stage runtime files from ODM after Android creates its encrypted data directories. ADB authentication remains enabled. [Clean-storage preflight](../packaging/stage-stability-runtime.sh) · [Runtime source](../runtime/encrypted-bootstrap/)
- Carry forward the r7 boot images and API 37.0 compatibility correction, plus the [Bluetooth SBC configuration](BLUETOOTH-SBC-OFFLOAD.md).

## Test limits

The first-boot USB helper logged an `IllegalArgumentException` when requesting its USB function combination. Authenticated ADB reconnected and all requested clean-install checks completed. Car Bluetooth audio and broader regression coverage remain untested for this installer. The shade traces are baseline measurements, with no new scheduler or GPU tuning in 1.2.

Video stutter remains open. All 15 local clips completed uninterrupted at FHD+, 480 dpi and fixed 60 Hz on Vulkan. Timing still showed brief frame-pacing hitches, and intermittent stutter remained in Facebook. [Video playback validation](VIDEO-PLAYBACK-VALIDATION.md#playback-follow-up)

## Local installer

The tested ZIP is **MonsterROM-p3s-SM-G998B-Stability-1.2-DEV-LOCAL.zip** (8,688,687,572 bytes).

```text
60ee841108861e293cef470f4dd351699c27141f2231e7774260f0aa7aa43c5d  MonsterROM-p3s-SM-G998B-Stability-1.2-DEV-LOCAL.zip
```

The hash identifies the tested local ZIP. This file stays local because it includes proprietary Samsung and Google binaries and a tester-specific public ADB key. GitHub carries the source and validation record.

## Reassembly

The [Stability 1.2 assembler](../packaging/assemble-stability12.py) requires a separately supplied Stability 1.1 template and the 1.2 partition images that match the [input manifest](../packaging/stability12-inputs.json). Use these private inputs with the MonsterROM host tools in the [r7 build guide](BUILD.md). The published recipe covers reassembly and validation with those inputs.

On Linux, place the three raw files `system.img`, `vendor.img` and
`odm.img` in the input directory and provide an existing output directory.

```sh
python3 packaging/assemble-stability12.py assemble \
  --base /inputs/Stability-1.1-DEV-LOCAL.zip --images /inputs/stability12 \
  --source /work/MonsterROM --output /releases/Stability-1.2-DEV-LOCAL.zip
```

The recipe takes the product and boot payloads from the pinned template. It
checks the whole-file recovery signature and the decoded partition hashes
before publishing the local output. ZIP metadata such as entry timestamps can
change the archive checksum during reassembly.

The embedded manifest records the status at assembly time. The input
manifest's separate reference-device record documents the later clean test of
the signed ZIP with that exact checksum.

For source integration, the final vendor image uses the matched r7 Mali
payload. Apply the display and camera patches to the matching SM-G998B port
sources. The tested [ODM init fragment](../runtime/encrypted-bootstrap/p3s-bootstrap.rc)
uses the KernelSU context for the post-encryption bootstrap and the shell
context for the display profile. In the tested ODM, `shell-profile.sh`
has the `system_file` SELinux label and the other runtime payloads have
`vendor_file` labels. The two VaultKeeper libraries and any opted-in ADB
public key are supplied locally. A source-only ROM build from this checkout
has not been validated.

## Installation requirements

The clean installer expects an unlocked SM-G998B on **G998BXXSJHZC2, bootloader revision 19** and compatible TWRP. The reference installation used Chiclet TWRP 3.7.1_12 v2. Keep the matching Samsung recovery firmware and a current off-device backup before using Format Data, which erases apps, accounts, settings, and internal storage. The installer checks freshly formatted, writable Data and Metadata before applying the images.
