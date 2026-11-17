# Post-r7 reference-device updates — through 16 November 2026

These are runtime changes verified on the maintainer's SM-G998B, not a new ROM release. The published r7 manifest and local r7 flashable ZIP are unchanged. No clean installer containing these later changes has been built or tested.

## SBC Bluetooth audio — 16 November

The laptop receiver reproduced silent SBC playback with Samsung hardware offload. The same clearer tone was audible through software encoding, silent with original offload restored, and audible again after disabling SBC offload only. The persistent Samsung offload capability is now `aptx-ssc-hifi`. Reconnect and persistent-storage readback passed; reboot, car media and HFP call audio remain untested. [Property source, evidence, application, clean-build guidance and rollback](BLUETOOTH-SBC-OFFLOAD.md). This workaround does not alter r7's ZIP.

## GPU r38p1

The reference handset upgraded from Mali r38p0 / Vulkan 1.1.213 to r38p1 / Vulkan 1.3.213. After reboot, all eight installed payload hashes matched the manifest; Vulkan enumeration succeeded, One UI Home and both physical display edges were normal, QHD+ 1440×3200 and 640 dpi were retained, and SELinux remained enforcing. No startup crash appeared in the captured crash buffer. This is a boot and activation check, not comprehensive graphics qualification or proof that video freezing is fixed.

Driver port credit: **EliteUI / elitetest1**. [Upstream release v1.3](https://github.com/elitetest1/GpuDriverUpdate_Exynos 2100/releases/tag/v1.3). The release describes r38p1 with Vulkan 1.3 for Exynos 2100. Samsung/Arm proprietary libraries are not included here. Attribution does not grant redistribution rights. [KernelSU module lifecycle reference](https://kernelsu.org/guide/module.html).

The downloaded archive SHA-256 is `ac6b3275922a38ec7ab9ae2b7b622d291e5c6ea9e8accf830b1c8c39fcc4d596`. [Manifest](../runtime/gpu-r38p1/manifest.json) contains original and replacement hashes. Four libraries cover 32/64-bit EGL and Vulkan; four XML files advertise Vulkan capabilities. ELF dependency comparison found no newly required shared-library names; that alone does not prove ABI compatibility.

### Reproduction and integration

Obtain the upstream archive separately and stage it outside this checkout:

```sh
python3 packaging/stage-gpu-update.py --archive /inputs/Exynos 2100-GPU-Drivers-v1.zip --output /work/p3s-gpu-r38p1
```

The helper validates archive and payload hashes and writes only to a new local directory. It does not contact, flash or modify a phone. Stage contents under `/data/adb/p3s-gpu-r38p1` on the matching reference ROM, root-owned, with scripts executable. Back up the original vendor files and existing boot hook off-device first. Run `sh /data/adb/p3s-gpu-r38p1/mount.sh /data/adb/p3s-gpu-r38p1 check` to validate the original files and payload without mounting.

The KernelSU module installer reported success on this port but left its update staged on reboot. Its normal module startup was not operating. That inactive duplicate was disabled. The working route uses the existing ODM `p3s-ce-profile` service, which invokes `/data/adb/post-fs-data.d/p3s-ce.sh` during post-fs-data. Immediately after its PATH assignment, the reference handset adds:

```sh
if ! /system/bin/sh /data/adb/p3s-gpu-r38p1/post-fs-data.sh; then log -t P3sGPU "GPU update skipped; original driver retained"; fi
```

Preserve all existing SDK, VaultKeeper, PIN/CE and display logic. Do not replace a live hook wholesale with the older r7 checkout copy. This integration is intentionally not added to r7's installer: r7 does not carry the proprietary payload or this update's qualification.

The loader verifies every original/replacement hash before binding files in init's mount namespace, assigns the existing library/config SELinux contexts, and rolls back mounts if the mount stage fails. It does not rewrite vendor, change GPU clocks, clear shader caches or disable thermal protections. A `trial-started` marker permits only one unverified boot. After successful activation, Home/display and crash checks, the reference handset creates `/data/adb/p3s-gpu-r38p1/verified` to retain the update. Do not create that marker before checking the trial.

### Rollback

As root, create `/data/adb/p3s-gpu-r38p1/disable`, then perform a normal reboot. The loader will leave the original vendor files in use. Do not live-unmount graphics libraries while Android is running. If an unverified trial fails, the next boot skips it automatically; recovery remains necessary if the handset cannot restart normally. Recovery can create the disable file only when Data is accessible. Keep the original matching recovery/firmware backups.

## ART/profile repair recorded on 14 November

The reference system image was repaired by adding a profile matched to the active framework, incorporating the already-tested PIN/display `services.jar`, and removing stale fs-verity metadata for these two changed files. The verified filesystem diff was limited to `system/etc/boot-image.prof`, its `.fsv_meta`, `system/framework/services.jar`, and its `.fsv_meta`.

| Artifact | SHA-256 |
|---|---|
| Repaired system image | `de37dcf2f76084b371436b88197c4679099c5e9756b1035951653661155f8103` |
| Matching boot profile | `965624b74fa8b6444a19dc2ea9ada2fc9d255fde8beaddedef1f4f205ae6653e` |
| services.jar | `4a9bf7ad445ee7389c3953ed416606ba9cdc7d6bf6ee4f38f871004fe0e578d2` |
| framework.jar used for matching | `e3fa11b4d7afa04f9afd1647c967d5f1ce61ab799b89041c90f0a2503d2cc042` |

Normal reboot/PIN-to-Home succeeded afterward. Avoid a framework-only/zygote restart: an earlier test produced a boot-check timeout. The binaries and original workspace-specific image-repair procedures remain local; this section records provenance, not a standalone rebuild recipe. This repaired image is not incorporated into the unchanged r7 ZIP. Matched shade repeats did not establish a reliable overall lag reduction.

## Unresolved video and other findings

- The user observed video freezing with continuing audio in multiple apps. It remains unresolved.
- Fixed 60 Hz and forced GPU composition did not resolve it. Those temporary settings were reverted. The Threads OpenGL comparison was inconclusive.
- Local H.264 and VP9 playback in Samsung Video, and local H.264 in Chrome, were smooth using Exynos hardware decoders before the GPU update. Forty-eight sampled vendor codec libraries/configs matched the S21 stock baseline; framework compatibility was not thereby proven.
- Internal recordings showed changing pictures when the user reported a physical-screen freeze. One trace lost its first seconds; a shorter follow-up retained them. Do not use the incomplete capture to rule out a startup fault.
- Display interrupts continued near 60 Hz and the controller error flag was zero. Requested DMA-fence events were unavailable and debugfs could not be mounted. These checks do not prove panel scanout is correct. A synchronized external-camera/internal capture is still needed.
- SBC media silence was reproduced and worked around using a laptop receiver, as documented above. The car head unit and HFP call audio remain untested. No 5G fix has been demonstrated.
- A battery voltage-reporting unit correction was drafted in a separate local kernel tree but was not built or flashed; it is not part of this update.

Recordings, private logs, firmware binaries, full ZIPs and signing keys remain local. GPU activation must not be advertised as a confirmed video-freeze fix.
