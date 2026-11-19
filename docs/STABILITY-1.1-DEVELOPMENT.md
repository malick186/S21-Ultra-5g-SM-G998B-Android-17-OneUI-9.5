# Stability 1.1 development integration

Historical development record. See [Stability 1.2](STABILITY-1.2.md) for the
verified clean installer and the current resolution and camera results.

The original Stability 1 candidate failed a clean boot because recovery populated /data/adb before init.usb.rc applied encryption=Require. The corrected installer must leave Data unpopulated; its preflight checks storage only. Small compatibility files are embedded in ODM and staged by Android after directory creation. The already-integrated services.jar does not need a second copy under Data.

The ODM updater must resolve map_partition("odm") after dynamic-partition changes. A raw mapper-path write initially passed transient readback but the next recovery showed old files. Both mapper and physical SUPER extent readback were subsequently checked.

The first root-context display attempt logged FAILED_TRANSACTION for cmd display/window. The existing shell-context diagnostic could access those services. Display and late debugging settings now run in shell context after sys.boot_completed, while privileged compatibility staging and the authenticated ADB-key copy retain their root service context. The physical device now fits, with live 1440x3200 mode/framebuffer content and density640. adb_enabled=1 and ro.adb.secure=1 were verified. A normal reboot to One UI Home passed: the user confirmed both physical edges fit; ADB reconnected authenticated; live mode/framebuffer bounds/content were 1440x3200, density640, active120Hz, adb_enabled=1, ro.adb.secure=1 and ro.secure=1. USB required a physical reconnect on this PC.

This is a local development build. Its ODM contains this tester's public ADB key, not the private key. Do not publish that personalized binary as a general release. Other builders must provide their own public key or retain normal interactive authorization. Never disable ADB authentication. Proprietary libraries and the full ROM remain local under the existing redistribution decision.

Bluetooth SBC workaround, API37.0, matched ART profile and tested services.jar remain in the base images. Video freezing is deferred and is not claimed fixed. A complete clean flash of the rebuilt 1.1 archive has not been performed; the running device received the same corrected ODM as a targeted update after clean installation.

The public [Stability 1.2 assembler](../packaging/assemble-stability12.py)
uses the retained private Stability 1.1 archive as its pinned template.
