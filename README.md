# MonsterROM Android 17 for Galaxy S21 Ultra 5G (Exynos)

**Target: Samsung SM-G998B, codename `p3s`. Current development release: Beta 2 r7, 14 November 2026.** This repository consolidates the source changes and runtime fixes tested on one SM-G998B. The repository URL uses “SM-G99B”; the supported hardware model is **SM-G998B**. Maintained here by **malick186**. This is an unofficial port built on MonsterROM and UN1CA.

**Release status:** Android reached One UI Home on the reference handset after the individual fixes. The API 37.0 correction was tested on the reference handset after reboot. The r7 installer integrates it directly into the system and product partitions. A clean r7 installation and first PIN unlock remain untested. Existing users of the working post-r5 setup have no reason to clean-flash solely to match this tag.

## Hardware, software and observed behavior

**Latest reference-device update (16 November 2026):** SBC Bluetooth media audio worked on a laptop receiver after disabling SBC hardware offload; the setting is saved persistently, but reboot and car-call testing remain open. [Workaround, comparison and rollback](docs/BLUETOOTH-SBC-OFFLOAD.md). This is a post-r7 runtime change, not a new flashable release.

**GPU reference-device update (15 November 2026):** Mali r38p1 / Vulkan 1.3 is active through a guarded, reversible early-boot loader. QHD+ and 640 dpi are retained. The ART/profile repair and GPU update are **post-r7 runtime changes**, not a new flashable release. Video freezing and shade lag remain unresolved. [Changes, validation, credits and rollback](docs/POST-R7-UPDATES.md).

| Area | What the port contains or the reference device demonstrated |
|---|---|
| Platform | Galaxy S26 SM-S942B ESSI donor, Android 17 / SDK 37, on S21 Ultra vendor hardware. One UI reports `90500`. MonsterROM describes this as a 9.5 backport based on One UI 9.0, with selected QPR2 components. |
| Kernel | Linux 5.4.304, Floppy v1.1.2-KN lineage, matched r54 Mali/vendor module set. Clang LTO and CFI enabled; SELinux enforcing. The published resolved kernel config matches the live device. |
| Boot and storage | Samsung vendor-boot layout, matched boot, DTBO and verification metadata, Android file-based encryption and target-specific VINTF checks. Keep the kernel and vendor ramdisk together. |
| Screen and touch | Physical QHD+ 1440 × 3200, 640 dpi override and adaptive refresh. QHD+ shade tests reached native 60 and 120 Hz. HD+ and FHD+ layout, group expansion, long messages and local inline replies were exercised at 640 dpi. Native panel switching at the two lower resolutions remains open. The retained profile reasserts QHD+ after boot. |
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

## Downloads and installation status

The later [post-r7 updates](docs/POST-R7-UPDATES.md) are documented separately with source-only GPU staging support. They have not been merged into or clean-flash-tested as a new full ROM ZIP. Driver binaries and full installers remain local.

The GitHub source archives contain the development project. For the recovery installer, the filename is **MonsterROM-p3s-SM-G998B-A17-beta2-r7.zip**. Check the SHA-256 against the release checksum before use. The installer is for an unlocked SM-G998B on **G998BXXSJHZC2, bootloader revision 19**, with a compatible TWRP that preserves boot. It checks these conditions before writing partitions. It does not install recovery, a modem or a bootloader.

The clean-test procedure requires an off-device backup and freshly formatted Data. Format Data **erases apps, settings and internal storage**. Recovery must mount real Data and Metadata read-write before installation. Formatting after installation removes runtime fixes. Use the original matching Samsung BL/AP/CP/CSC repair set as the recovery route. A complete r7 clean flash has not yet been validated, so this is a development candidate.

[Release page](https://github.com/malick186/S21-Ultra-5g-SM-G99B/releases) · [Installer checksum](docs/MonsterROM-p3s-SM-G998B-A17-beta2-r7.zip.sha256) · [Build instructions](docs/BUILD.md)

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
