# SBC Bluetooth media-audio workaround

Validated on the reference SM-G998B port on 16 November 2026; documented on 17 November. This is a post-r7 runtime workaround, not a new ROM release or a repair to the underlying proprietary offload implementation.

## Confirmed failure and comparison

A Windows laptop acting as an A2DP receiver negotiated SBC at 44.1 kHz, 16-bit stereo. The phone routed unmuted media to Bluetooth, while the Samsung vendor audio HAL repeatedly logged `skip to write by BT A2DP Off/suspended state or usb disconnection state`. Framework A2DP suspension flags were false.

The first test clip had a tone peaking at -48 dB, so its listening result was inconclusive. Testing was repeated with the same clearer 660 Hz AAC tone for each comparison:

| Configuration | Observed result |
|---|---|
| Software encoding | Tone audible from laptop speakers |
| Original Samsung offload capability list restored | Tone silent; HAL write-skipping messages returned |
| SBC removed from offload list, Bluetooth reconnected | Tone audible again; software audio session started successfully |

The final logs reported `offloadMode false`, `btOffload = 0`, and `A2DP_SOFTWARE_ENCODING_DATAPATH` reaching `STARTED`. The user confirmed the audible results on the physical laptop. This isolates a failing SBC offload path on this port; it does not identify the precise binary or firmware incompatibility.

## Applied property

[Property source](../runtime/bluetooth-sbc-offload/system.prop):

```properties
persist.bluetooth.samsung.a2dp_offload.cap=aptx-ssc-hifi
```

The original runtime default was `sbc-aptx-ssc-hifi`; there was no original entry in persistent storage. Removing `sbc` keeps SBC available through software encoding and retains the other offload capability entries. AptX, SSC and HiFi paths were not tested. Software encoding may increase CPU use or battery consumption; this has not been measured.

The standard `persist.bluetooth.a2dp_offload.disabled` temporary comparison did not switch this build's actual path; that temporary property was removed. Samsung's capability property was identified by inspecting the installed Bluetooth implementation's `A2dpService.isOffloadSupportedCodec` behavior. No proprietary APK, disassembly or driver binary is distributed here.

## Apply to the matching reference port

Save the current runtime and persistent values before changing anything. These commands require root and the reference KernelSU installation's resetprop binary:

```sh
su
/data/adb/ksu/bin/resetprop persist.bluetooth.samsung.a2dp_offload.cap
/data/adb/ksu/bin/resetprop -P persist.bluetooth.samsung.a2dp_offload.cap
# On the tested device the second command reported no persistent entry.
/data/adb/ksu/bin/resetprop -n -p persist.bluetooth.samsung.a2dp_offload.cap aptx-ssc-hifi
/data/adb/ksu/bin/resetprop -P persist.bluetooth.samsung.a2dp_offload.cap
```

Turn Bluetooth off, wait for it to finish stopping, then turn it on and reconnect the media receiver. Replay an audible local clip and confirm sound on the receiver, not only a connected icon. QHD+ 1440 x 3200, 640 dpi and user data were retained.

Persistent-storage readback and reconnect were verified. A full phone reboot with this workaround has **not** yet been tested.

## Future clean-build integration

Use the supplied property assignment as the SM-G998B product's default during property generation, replacing any existing assignment for this key rather than appending duplicates. The `system.prop` filename is a source fragment, not an automatically installed KernelSU module; this checkout does not automatically consume it. The old r7 installer and ZIP are unchanged.

Before packaging a future release, inspect the final image property files for the intended single effective value. Validate a clean install, a normal reboot, Bluetooth reconnect, audible SBC playback and switching back to the phone speaker. Existing persistent values can override image defaults; preserve and explicitly migrate or retain them as appropriate for an upgrade. Do not silently overwrite a user's different custom profile.

## Rollback on the reference device

Because this device originally had no persistent entry, restore it with:

```sh
su
/data/adb/ksu/bin/resetprop -n -p --delete persist.bluetooth.samsung.a2dp_offload.cap
/data/adb/ksu/bin/resetprop -n persist.bluetooth.samsung.a2dp_offload.cap sbc-aptx-ssc-hifi
```

Then cycle Bluetooth and reconnect. On another installation, restore that installation's recorded values instead. If a future image incorporates the workaround as its default, deleting the persistent entry alone will not restore the older default after reboot.

## Remaining qualification and references

- Car media playback remains untested with this workaround. The saved car connection had also negotiated SBC, making a car retest relevant, but laptop success does not establish car success.
- HFP/SCO call audio, other codecs, long-duration playback and reboot persistence remain untested.
- This change does not fix the separate video-freezing issue or establish a kernel fault.
- The local diagnostic, recordings and device-identifying logs remain private. No full ROM ZIP is published by this update.

The laptop receiver used Microsoft's documented [AudioPlaybackConnection API](https://learn.microsoft.com/en-us/windows/apps/develop/media-playback/enable-remote-audio-playback). Property application used the existing KernelSU installation's resetprop implementation. Samsung supplies the Bluetooth and vendor audio components; this project contributes the configuration workaround and test documentation, without claiming ownership of those components.
