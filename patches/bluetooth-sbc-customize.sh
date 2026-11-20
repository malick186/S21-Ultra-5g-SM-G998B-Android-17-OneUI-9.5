# SM-G998B: SBC A2DP software-encoding workaround.
# Validated against laptop receiver; car and HFP remain untested.
# Replace the donor product default; do not modify kernel/audio drivers.
SET_PROP "product" "persist.bluetooth.samsung.a2dp_offload.cap" "aptx-ssc-hifi"
