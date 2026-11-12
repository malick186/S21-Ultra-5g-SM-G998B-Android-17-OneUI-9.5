#!/system/bin/sh
export PATH=/system/bin:/vendor/bin
flag=/metadata/p3s-ce-display.enabled
[ "$(getprop ro.product.vendor.model)" = SM-G998B ] || exit 0
[ "$(getprop ro.build.version.incremental)" = "S942BXXU5CZJJ" ] || exit 0
while [ -f "$flag" ] && [ "$(getprop sys.boot_completed)" != 1 ]; do sleep 5; done
while [ -f "$flag" ]; do
    size=$(settings get global display_size_forced) || exit 1
    density=$(settings --user 0 get secure display_density_forced) || exit 1
    if [ "$size" != "1440,3200" ] || [ "$density" != 640 ]; then
        service call window 16 i32 0 i32 1440 i32 3200 i32 640 i32 1 i32 -1 >/dev/null
        log -t P3sDisplay "Restored QHD+ and 640 dpi"
    fi
    sleep 30
done
