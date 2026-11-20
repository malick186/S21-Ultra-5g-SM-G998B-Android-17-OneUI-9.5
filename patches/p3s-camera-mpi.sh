
# SM-G998B Night processing: retain the wrapper matching the restored MPI30 plugins.
ADD_TO_WORK_DIR "$TARGET_FIRMWARE" "system" "system/lib64/libAIQSolution_MPI.camera.samsung.so" 0 0 644 "u:object_r:system_lib_file:s0"
ADD_TO_WORK_DIR "$TARGET_FIRMWARE" "system" "system/lib64/libMultiFrameProcessing30.snapwrapper.camera.samsung.so" 0 0 644 "u:object_r:system_lib_file:s0"
for CAMERA_MPI_LIBRARY in libAIQSolution_MPI.camera.samsung.so libMultiFrameProcessing30.camera.samsung.so libMultiFrameProcessing30.snapwrapper.camera.samsung.so libLocalTM_pcc.camera.samsung.so libSwIsp_wrapper_v1.camera.samsung.so; do
    if ! grep -Fxq "$CAMERA_MPI_LIBRARY" "$WORK_DIR/system/system/etc/public.libraries-camera.samsung.txt"; then
        printf '%s\n' "$CAMERA_MPI_LIBRARY" >> "$WORK_DIR/system/system/etc/public.libraries-camera.samsung.txt"
    fi
done
unset CAMERA_MPI_LIBRARY
