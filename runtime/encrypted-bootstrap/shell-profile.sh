#!/system/bin/sh
export PATH=/system/bin:/vendor/bin
apply_resolution() {
 selected=$(settings get global display_size_forced) || return 1
 case "$selected" in
  720,1600) width=720; height=1600; desired_density=320 ;;
  1080,2400) width=1080; height=2400; desired_density=480 ;;
  1440,3200|null) width=1440; height=3200; desired_density=640 ;;
  *) log -t P3sDisplay "Unsupported resolution; leaving it unchanged"; return 1 ;;
 esac
 rate=120.00001
 [ "$(settings get system refresh_rate_mode)" = 0 ] && rate=60.000004
 timeout 10 cmd display set-user-preferred-display-mode "$width" "$height" "$rate" 0 false || return 1
 timeout 10 service call window 16 i32 0 i32 "$width" i32 "$height" i32 "$desired_density" i32 1 i32 -1 || return 1
 log -t P3sDisplay "Aligned selected ${width}x${height} at ${desired_density} dpi"
}
save_lines() {
 index=0
 while IFS= read -r line && [ "$index" -lt 24 ]; do
  while [ -n "$line" ] && [ "$index" -lt 24 ]; do
   part=$(printf '%s' "$line" | cut -c1-78)
   setprop "debug.p3s.fix.status.$index" "$part" || return 1
   line=${line#"$part"}; index=$((index+1))
  done
 done
}
{
 echo SHELL_PROFILE_BEGIN
 id
 apply_resolution
 timeout 10 settings put global development_settings_enabled 1
 timeout 10 settings put global adb_enabled 1
 timeout 10 svc usb setFunctions mtp,adb
 sleep 3
 wm size; wm density
 printf 'adb_enabled=%s\n' "$(settings get global adb_enabled)"
 printf 'usb=%s\n' "$(getprop sys.usb.config)"
 cmd display get-user-preferred-display-mode 0
 dumpsys SurfaceFlinger | grep -E 'activeMode=|framebufferSpace=' | head -4
 echo SHELL_PROFILE_END
} 2>&1 | save_lines
setprop debug.p3s.fix.done 1
# Watch preferences, not frames. Samsung can adjust density during a resolution
# change; wait for that transaction, then keep QHD+/640-equivalent visual size.
last=''
while [ "$(getprop sys.boot_completed)" = 1 ]; do
 selected=$(settings get global display_size_forced) || exit 1
 density=$(settings --user 0 get secure display_density_forced) || exit 1
 case "$selected" in
  720,1600) desired_density=320 ;;
  1080,2400) desired_density=480 ;;
  1440,3200|null) desired_density=640 ;;
  *) sleep 3; continue ;;
 esac
 if [ "$selected" != "$last" ] || [ "$density" != "$desired_density" ]; then
  sleep 2
  apply_resolution >/dev/null 2>&1 && last=$(settings get global display_size_forced)
 fi
 sleep 3
done
