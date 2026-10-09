#!/bin/bash
# P4 detection vs eye depth with the flux-based signal model (same LED power unless LED_SCALE given)
run(){ tag=$1; shift; env FLUX_MODE=1 FLUX_E=83700 "$@" python3 detect_vs_depth.py > ../results/dvdflux_${tag}.log 2>&1; }
run D3_b0 DESIGN=design3_final FOCUS_BIAS=0 &
run 4A_b0 DESIGN=design4A FOCUS_BIAS=0
wait
run D3_b05 DESIGN=design3_final FOCUS_BIAS=0.5 &
run 4A_b05 DESIGN=design4A FOCUS_BIAS=0.5
wait
run 4A_halfLED_b0 DESIGN=design4A FOCUS_BIAS=0 LED_SCALE=0.49 &
run 4AD10_b0 DESIGN=design4A_D10 FOCUS_BIAS=0
wait
run 3B_b0 DESIGN=design3B FOCUS_BIAS=0 &
run 4AD12_b0 DESIGN=design4A_D12 FOCUS_BIAS=0
wait
echo ALLDONE
