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

Each row compares the same files under the two refresh policies. The 60 fps clip accounted for 36 of the 38 skips with the 60 Hz adaptive minimum. The reference phone entered a one-day fixed-60 Hz trial after the controlled tests. Everyday playback, battery impact, and behavior at other resolutions are still awaiting validation. Fixed refresh is a workaround for the tested local playback, and the general video-stutter issue remains open.

## Separate audio startup test

Reducing the PCM buffer request from 500 ms to 200 ms lowered the median per-clip startup frame gap from 134.10 ms to 56.75 ms across the same 15 local files. This metric is the largest gap among the first 12 video buffers latched in each clip, summarized as the median across clips. Two clips had a steady-playback gap over 80 ms in each run. The original 500 ms setting was restored. Bluetooth audio was untested.

## Release status

The tests used runtime settings on the reference build. A separate TWRP add-on requires a verified fix in an affected app, regression testing at HD+, FHD+, and QHD+, and a tested rollback. [Stability 1.2 clean-install validation](STABILITY-1.2.md)
