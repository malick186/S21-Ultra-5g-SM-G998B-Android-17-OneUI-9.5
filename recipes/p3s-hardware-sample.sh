#!/system/bin/sh
# Runs once as Android's shell user. Only selected diagnostic fields leave the pipeline.
export PATH=/system/bin:/vendor/bin
save_lines() {
    group=$1
    index=0
    while IFS= read -r line && [ "$index" -lt 24 ]; do
        while [ -n "$line" ] && [ "$index" -lt 24 ]; do
            part=$(printf '%s' "$line" | cut -c1-78)
            setprop "debug.p3s.audit.$group.$index" "$part" || return 1
            line=${line#"$part"}
            index=$((index+1))
        done
    done
}
{
    timeout 4 wm size
    timeout 4 wm density
    printf 'font_scale=%s\n' "$(timeout 3 settings get system font_scale)"
    timeout 5 dumpsys window displays | grep -E 'init=[0-9]+x|mDisplayFrames|mCurrentFocus' | head -4
    timeout 5 dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp' | head -2
} 2>&1 | save_lines display
{
    timeout 6 dumpsys input | grep -E 'SurfaceWidth:|SurfaceHeight:|PhysicalWidth:|PhysicalHeight:|Viewport INTERNAL|logicalFrame=|Orientation:|XScale:|YScale:|AssociatedDisplay:|sec_touchscreen' | head -32
} 2>&1 | save_lines input
{
    for key in gsm.sim.state gsm.network.type gsm.version.baseband init.svc.vendor.ril-daemon init.svc.ril-daemon; do
        printf '%s=%s\n' "$key" "$(getprop "$key")"
    done
    timeout 6 dumpsys telephony.registry | grep -Eo 'mSimState=[0-9]+|mDataConnectionState=-?[0-9]+|mRadioPowerState=[0-9]+|mVoiceRegState=[0-9]+|mDataRegState=[0-9]+' | sort -u
    timeout 5 service list | grep -E 'android.hardware.radio.(sim|modem).*slot' | head -4
} 2>&1 | save_lines radio
setprop debug.p3s.audit.sample done
