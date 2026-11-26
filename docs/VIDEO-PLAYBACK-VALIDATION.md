# Stability 1.2 video playback validation

Testing on 24–25 November 2026 reproduced visible video stutter while audio continued on one Exynos Galaxy S21 Ultra (SM-G998B) running Stability 1.2 DEV LOCAL. All runs used FHD+ at 480 dpi, local test clips, and the phone speaker.

## Display presentation

The decoder continued submitting video frames during the stutter. In the traced clips, SurfaceFlinger sometimes received two successive buffers in one update and latched the newer buffer. Skipped buffers were counted by gaps in sequence numbers on the same video layer. Playback completion and decoder drop counters alone missed this behavior. [Android display refresh-rate documentation](https://source.android.com/docs/core/graphics/multiple-refresh-rate)

| Refresh policy | Clips | Submitted frames | Skipped with original adaptive refresh | Skipped in comparison run |
| --- | ---: | ---: | ---: | ---: |
| Fixed 60 Hz | 4 | 1,012 | 115 | 4 |
| Fixed 120 Hz | 15 | 2,992 | 172 | 8 |
| Adaptive with a 60 Hz minimum | 15 | 2,992 | 172 | 38 |
| Adaptive with a 96 Hz minimum | 5 | 1,262 | 127 | 12 |

Each row compares the same files under the two refresh policies. The 60 fps clip accounted for 36 of the 38 skips with the 60 Hz adaptive minimum. The reference phone entered a one-day fixed-60 Hz trial after the controlled tests. The follow-up below covers local clips and selected Facebook playback. Battery impact and behavior at other resolutions remain unverified. Fixed refresh is a workaround for the tested local playback, and the general video-stutter issue remains open.

## Separate audio startup test

Reducing the PCM buffer request from 500 ms to 200 ms lowered the median per-clip startup frame gap from 134.10 ms to 56.75 ms across the same 15 local files. This metric is the largest gap among the first 12 video buffers latched in each clip, summarized as the median across clips. Two clips had a steady-playback gap over 80 ms in each run. The original 500 ms setting was restored. Bluetooth audio was untested.

## Playback follow-up

In the 26–27 November 2026 follow-up, the reference handset replayed all 15 local clips uninterrupted on Vulkan using TextureView, FHD+ (1080 × 2400), 480 dpi, fixed 60 Hz, and the normal scheduler. The player reported zero buffering events and zero dropped frames. The trace measured time between consecutive app-window buffers latched by SurfaceFlinger within each clip.

| Interval | Gaps of at least 80 ms | Observation |
| --- | ---: | --- |
| Near clip starts | 6 | Short startup pacing hitches. |
| Steady playback | 1 | 81.35 ms in AV1 clip 14 while the decoder continued to release frames. |
| Near clip ends | 1 | About 99 ms in VP9 clip 13 after the last video frames had already decoded. |

The longest decoder release gap during steady playback was 61.50 ms. Measured app-window gaps were all below 150 ms. The 60 fps HEVC clip released all 480 source frames and produced 407 distinct TextureView updates, so the player’s drop counter alone cannot establish presentation of every frame.

### Output surface and scheduling trials

Replaying all 15 clips in the diagnostic player with SurfaceView reduced its longest steady video-layer latch interval to 66.47 ms. The matched AVC and AV1 comparison also removed the 80 ms or longer gaps observed on TextureView. This was a playback path available to the diagnostic player. [Android video surface guidance](https://developer.android.com/media/media3/ui/surface)

Kernel tracing showed that CPU 7 going offline could restore CPU 0 to RenderThread’s allowed set when cpuset work reapplied the group’s effective mask. A temporary child cpuset held the expected mask across 23 observed hotplug transitions, although two brief CPU 0 runs remained near clip endings. A later Facebook test still stuttered with zero RenderThread time on CPU 0. A separate priority trial reduced runnable waits, with residual frame gaps. The original scheduling policy was restored and the temporary group was removed. [Kernel cpuset source](https://github.com/FlopKernel-Series/flop_exynos2100_kernel/blob/113ce9d986f74e1526981324ec164e4d90930071/kernel/cgroup/cpuset.c#L1061)

### Facebook playback

During active Stories playback, one 85 ms presentation gap contained three video releases. About 15 ms of that interval was spent waiting for an app Binder thread during buffer handoff. A separate 1.16-second gap followed Facebook closing its player window, seeking, and starting a new decoder. The same video also played smoothly on a later replay. These observations distinguish individual presentation delays from player transitions and leave the intermittent stutter open.

## Release status

The latest update records validation. The Stability 1.2 installer and its checksum are unchanged. A separate TWRP add-on requires a verified fix in an affected app, regression testing at HD+, FHD+, and QHD+, and a tested rollback. [Stability 1.2 clean-install validation](STABILITY-1.2.md)
