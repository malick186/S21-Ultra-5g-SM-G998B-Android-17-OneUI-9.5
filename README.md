# Samsung Galaxy S21 Ultra 5G SM-G998B: MonsterROM Android 17

**Stability 1.2 DEV LOCAL** passed a clean install on the Exynos Galaxy S21 Ultra **SM-G998B** (`p3s`) on 20 November 2026. Setup Wizard reached One UI Home, all three display modes fit and responded to touch, and Night mode completed a 12-frame capture and saved an openable JPEG. [Stability 1.2 validation and sources](docs/STABILITY-1.2.md)

This repository contains the source changes and validation notes from one reference handset. This is an unofficial Android 17 custom ROM port based on MonsterROM and UN1CA, maintained here by **malick186**.

## Quick navigation

- [Device compatibility and requirements](#device-compatibility-and-requirements)
- [Hardware, software and observed behavior](#hardware-software-and-observed-behavior)
- [Version history](#version-history)
- [Releases and installation status](#releases-and-installation-status)
- [Frequently asked questions](#frequently-asked-questions)
- [Source and credits](#source-and-credits)

## Device compatibility and requirements

| Item | Reference setup |
|---|---|
| Device | Samsung Galaxy S21 Ultra 5G **SM-G998B** (`p3s`, Exynos 2100) |
| Firmware | `G998BXXSJHZC2`, bootloader revision **19** |
| Recovery | Unlocked bootloader and compatible TWRP |
| Latest documented development build | **Stability 1.2 DEV LOCAL**, clean-install tested on one reference handset |

Other model numbers, including Snapdragon variants, have not been validated. See the [installation requirements](docs/STABILITY-1.2.md#installation-requirements) before considering a flash. Format Data erases internal storage, apps, accounts and settings; keep a current off-device backup.

## Hardware, software and observed behavior

| Area | What the port contains or the reference device demonstrated |
|---|---|
| Platform | Galaxy S26 SM-S942B ESSI donor, Android 17 / SDK 37, on S21 Ultra vendor hardware. One UI reports `90500`. MonsterROM describes this as a 9.5 backport based on One UI 9.0, with selected QPR2 components. |
| Kernel | Linux 5.4.304, Floppy v1.1.2-KN lineage, matched r54 Mali/vendor module set. Clang LTO and CFI enabled; SELinux enforcing. The published resolved kernel config matches the live device. |
| Boot and storage | Samsung vendor-boot layout, matched boot, DTBO and verification metadata, Android file-based encryption and target-specific VINTF checks. Keep the kernel and vendor ramdisk together. |
| Screen and touch | Stability 1.2 passed physical switching and touch checks through Settings in HD+ (720 × 1600 at 320 dpi), FHD+ (1080 × 2400 at 480 dpi) and QHD+ (1440 × 3200 at 640 dpi). The density tracks the selected resolution to keep the interface the same size. |
| Graphics and camera | Stability 1.2 restores the matched Mali r38p0 stack in place of the r38p1 update. After the clean flash, a Night capture processed all 12 frames, completed denoising and saved a 4000 × 3000 JPEG with `NO_ERROR`. |
| Unlock and telephony | A private PIN opened credential-encrypted storage and One UI Home after restart. The S21 stock VaultKeeper client and HIDL library were restored ahead of framework startup. Slot 1 registered on LTE. 5G registration, payment certification and broad carrier compatibility remain unverified. |
| Root and performance | KernelSU Next root worked on the reference phone. System UI uses its original APK. Grouped-notification remeasurement and occasional missed frames remain measurable at QHD+. |

## Version history

| Revision | Changes and outcome |
|---|---|
| Earlier UN1CA 3.2.x setup (Android 16) | Used as an Exynos reference and rollback environment. Earlier recovery, root and GPU driver experiments belong to that setup. |
| Initial A17 candidate / r1 era | Adapted the MonsterROM SDK37 build for p3s. Established donor/target identities, encryption and SELinux checks, ARM64/legacy-provider review, and the matching kernel/module build. |
| r2 | Added target VINTF and firmware guards. The installer completed, but the device stalled before boot animation, including after a clean install. Stock restoration was required. |
| Beta 2 r3 | Corrected Samsung vendor-boot packing, including alignment, load addresses and board metadata. Added archive/layout verification and a separate recovery control. An inherited recovery script repacked stock boot. |
| Beta 2 r4 | Removed automatic boot repacking and revised the recovery unlock-property guard. TWRP opened; returning to stock Android under the test verification metadata failed. |
| Beta 2 r5 | Corrected the top-level verification profile and retained the original signed chained metadata. A clean install reached a built-in initialization CFI panic. The original r5 ZIP alone is unsuitable for installation. |
| Post-r5 kernel and driver series | Corrected built-in and module initialization dispatch; fixed startup entry points in USB-C PD notification and GPU cooling, plus the analogous optical flicker driver. Added persistent console diagnostics. Corrected the checked `default_llseek` entry and separated the embedded kernel config data from its CFI-instrumented proc reader. Android then reached setup. |
| Post-r5 framework and device fixes | Added early startup/hardware diagnostics, corrected the PIN-to-CE storage handoff, restored the S21 VaultKeeper libraries during startup, and retained the QHD+/640 dpi display profile. Verified touch on the shade, LTE and PIN-to-Home on the reference device. |
| Post-r5 shade experiments | Tested renderer and compilation behavior, conversation-icon layout guards and group-count label guards. The last guard skipped two redundant writes per measured final rebuild, but late frames did not improve. The original System UI was restored. SQL and reverted patches are retained under `tests/shade/`. |
| **Beta 2 r6** | Consolidated the working boot, vendor boot, DTBO, ODM, verification images and runtime fixes into one recovery ZIP. Added input pinning, clean-storage checks and release verification. The installer stages the runtime files before flashing partitions. This packaging step requires its own clean-install test. |
| **Beta 2 r7** | Corrects the public minor SDK to the donor’s Android 17 API 37.0 across system, embedded system_ext and product. The former 37.2 label led Maps to load a missing MemoryBudgetManager class. Play services also logged a missing SignedPackageWithMetadata class. With the equivalent boot-time correction, Maps cold-launched and accepted a location search, and Google Settings opened without either exception during the test window. The clean installer sets the values in the images before first boot and does not require a root script for this correction. |
| Post-r7 runtime updates | Added the reversible Mali r38p1 experiment and the SBC software encoding workaround. Laptop Bluetooth media playback and reconnect passed during the SBC test. [GPU and ART changes](docs/POST-R7-UPDATES.md) · [SBC test and rollback](docs/BLUETOOTH-SBC-OFFLOAD.md) |
| **Stability 1.2 DEV LOCAL** | Consolidates the encryption-safe installer staging, active display geometry, proportional resolution profile, and Night camera dependencies with the matched Mali r38p0 stack. Carries forward API 37.0 and the SBC configuration. The complete installer passed the requested clean-install checks on one reference phone. [Validation](docs/STABILITY-1.2.md) |

## Releases and installation status

The [Stability 1.2 GitHub release](https://github.com/malick186/S21-Ultra-5g-SM-G998B-Android-17-OneUI-9.5/releases/tag/stability-1.2) provides the source archive and release notes. The tested Stability 1.2 recovery ZIP, **MonsterROM-p3s-SM-G998B-Stability-1.2-DEV-LOCAL.zip**, stays local because it contains proprietary firmware and apps and a tester-specific public ADB key. Its SHA-256 and installation requirements are recorded in the [Stability 1.2 notes](docs/STABILITY-1.2.md).

The [key-free local installer recipe](docs/SHARING-STABILITY-1.2.md) removes
the tester's ADB authorization and leaves USB debugging under Android's
normal user control.

The historical Beta 2 r7 release remains available with its [installer checksum](docs/MonsterROM-p3s-SM-G998B-A17-beta2-r7.zip.sha256) and [build instructions](docs/BUILD.md). The complete r7 installer has separate validation status from Stability 1.2.

## Frequently asked questions

### Is this an official Samsung Android 17 update?

No. This is an unofficial development port based on MonsterROM and UN1CA.

### Does GitHub include a flashable ROM?

No. The [Stability 1.2 prerelease](https://github.com/malick186/S21-Ultra-5g-SM-G998B-Android-17-OneUI-9.5/releases/tag/stability-1.2) provides source and release notes. The tested recovery ZIP is not published.

### What has been tested?

The clean install reached One UI Home on one SM-G998B. Touch worked in HD+, FHD+ and QHD+, and the saved Night mode photo opened. This does not establish daily-driver readiness. Video freezing remains deferred, and in-car Bluetooth audio and broader regression coverage remain untested for this installer. See the [test limits](docs/STABILITY-1.2.md#test-limits).

## Source and credits

The optional Exynos 2100 GPU update is ported by **EliteUI / elitetest1**: [upstream r38p1 release](https://github.com/elitetest1/GpuDriverUpdate_Exynos2100/releases/tag/v1.3). Only the local guarded loader and hash manifest are published here; Samsung/Arm driver binaries are excluded.

| Component | Source and attribution |
|---|---|
| ROM framework | Salvo Giangreco and UN1CA contributors, original build and patch system. [UN1CA](https://github.com/salvogiangri/UN1CA) · [S21 Ultra XDA thread](https://xdaforums.com/t/4773336/) |
| Android 17 port | ditternation / devcore94, MonsterROM `seventeen` at `9353588dce5cd12baebbb0effa124372e45544cf`. [Pinned MonsterROM source](https://github.com/devcore94/MonsterROM/tree/9353588dce5cd12baebbb0effa124372e45544cf) |
| Kernel | Flopster101 and FlopKernel-Series contributors, Samsung Exynos sources and Linux contributors. [Pinned Floppy source](https://github.com/FlopKernel-Series/flop_exynos2100_kernel/tree/113ce9d986f74e1526981324ec164e4d90930071) · [Local kernel changes](patches/kernel.patch) · [Exact config](kernel.config) |
| Firmware | Samsung Electronics and component licensors. Target SM-G998B/AUT/G998BXXSJHZC2; actual donor archive SM-S942B/INS/S942BXXU5BZJA. The running donor framework reports S942BXXU5CZJJ. Preserve the distinction when comparing builds. [Samsung Open Source](https://opensource.samsung.com/) |
| Android, build and validation tools | AOSP, Android Clang, mkbootimg, AVB, signapk, Perfetto, Apktool, erofs-utils, img2sdat, samloader and their maintainers. [Pinned tools](docs/submodule-lock.txt) · [Tool repositories](docs/rom-submodules.ini) · [Compiler and kernel inputs](docs/kernel-inputs.json) |
| Root and recovery | KernelSU Next contributors and Team Win Recovery Project. The local recovery control inherited the handset's existing recovery image; its original device-builder attribution was not independently established. Recovery is distributed separately from the port by its respective maintainers. [KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next) · [TWRP](https://twrp.me/) |
| Additional upstream credits | The original acknowledgements include ShaDisNX255, DavidArsene, paulowesll, Simon1511, ananjaser1211, Fede2782, iDrinkCoffee, RisenID and LineageOS. [Upstream acknowledgements and tool licenses](docs/MonsterROM-upstream.md#credits) |

ROM build code carries the upstream GPLv3 terms. Linux kernel sources carry GPL-2.0 terms with the documented exceptions. Applicable notices and copyright headers remain with each component. Samsung/Google firmware, proprietary apps, bootloader files and signing credentials have separate terms. Source credits do not grant a binary redistribution license or imply endorsement by XDA, Samsung or the upstream maintainers. [License texts](licenses/)
