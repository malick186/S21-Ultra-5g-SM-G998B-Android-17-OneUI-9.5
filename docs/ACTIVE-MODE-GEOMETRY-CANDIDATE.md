# SM-G998B active-mode geometry correction

The installed update passed physical edge checks in QHD+, FHD+ and HD+ on
the owner's SM-G998B on 20 November 2026. Android also retained HD+ and its
320 dpi density after a normal restart, with matching output and composition
dimensions.

The owner confirmed on 20 November 2026 that consistent visual size is wanted:
QHD+ 1440×3200 at 640 dpi, FHD+ 1080×2400 at 480 dpi, HD+ 720×1600 at 320 dpi.
This supersedes the earlier literal-640-at-every-resolution interpretation.
These pairs all retain 360 dp of logical width.

The donor services.jar's internal display path uses default-mode dimensions
when FW_DYNAMIC_RESOLUTION_CONTROL is enabled. On this port a live FHD+ trace
showed a 1080×2400 output with a 1440×3200 composition rectangle. A temporary
QHD+ selection and normal reboot restored physical edge fit according to the
owner. It did not establish correct HD+/FHD+ switching.

The candidate changes only that geometry decision in
LocalDisplayAdapter$LocalDisplayDevice.getDisplayDeviceInfoLocked to use its
existing active-mode path. This follows the upstream Android implementation:
https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android16-release/services/core/java/com/android/server/display/LocalDisplayAdapter.java

Input services.jar SHA256:
4a9bf7ad445ee7389c3953ed416606ba9cdc7d6bf6ee4f38f871004fe0e578d2
Candidate services.jar SHA256:
c8c5b0622049c174bbeb84d4e4aea08424315bb0fc43ca873f27adf8058b0dac

Only classes.dex differs among JAR entries. Disassembly roundtrip confirms all
other classes are identical; the edited class matches its input control flow
after normalizing relocated branch labels. Other framework fixes are retained.
No kernel change, data format, encryption bypass or SELinux relaxation is used.

The accompanying ODM candidate labels its shell-readable display script as
system_file rather than vendor_file. The previous script failed with permission
denied and did not run. The profile retains any of the three supported user
resolution choices and applies its proportional density; its former QHD-only
guard remains inert. Settings switched from QHD+ to FHD+ and then HD+ with
matching hardware, layer-stack and framebuffer rectangles at each resolution.
The owner confirmed that both edges fit in all three modes and that touch
worked in FHD+ and HD+.

Full binaries and private logs stay local. Proprietary services.jar remains
Samsung-owned; this repository contains the narrow patch, not the binary.
