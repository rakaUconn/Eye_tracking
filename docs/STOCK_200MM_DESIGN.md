# Stock-lens variant with eye -> first lens ~ 205 mm (two AC254-150-B)

Search: 118 + configurations (`src/opt200.py`, `refine200b.py`), eye->first lens constrained to 195-205 mm, final layout model
(filter at the stop, cover glass on the sensor). Result files: `results/stock200_final.json`, `stock200_refined_eyelens.json`,
`sim_*_stock200_final.*`. Same caveats as `STOCK_LENS_BUILD_GUIDE.md` (glass data from memory, doublet thickness split assumed, placeholders for filter/cover).

## Prescription (one channel, unfolded, mm)
| # | Item | Radius | Thickness | Glass | Note |
|---|---|---|---|---|---|
| OBJ | eye plane | inf | **201.14** | - | eye -> stop |
| 1 | CB | - | 0 | - | decenter X -6.5 |
| 2 | STOP (diam 6.25) + filter | inf | 3.0 | N-BK7 proxy | |
| 3 | air | inf | **0.86** | - | |
| 4 | CB | - | 0 | - | decenter X +6.5 (pick-up, scale -1) |
| 5 | AC254-150-B A, R1 (standard orientation: crown face toward the eye) | +91.6 | 5.4 | N-BK7 | split assumed |
| 6 | | -66.7 | 2.5 | SF5 | |
| 7 | | -197.7 | **0.30** | - | |
| 8 | AC254-150-B B, same orientation | +91.6 | 5.4 | N-BK7 | |
| 9 | | -66.7 | 2.5 | SF5 | |
| 10 | | -197.7 | **112.51** | - | to cover glass |
| 11 | cover glass | inf | 1.0 | N-BK7 proxy | |
| 12 | gap | inf | 0.5 | - | |
| IMA | sensor | | | | |

Eye -> first lens = 201.14 + 3.0 + 0.86 = **205.0 mm** (constraint bound). Folded: eye->M1 30, M1->V 25.0, V->stop 146.14 mm (30 + 25 + 146.14 = 201.14).
Two identical, stock, same-orientation doublets: one part number to order; spacer ring between lenses about 3 mm (gap 0.30 plus edge sags; verify with STEP).

## Predicted performance
| Item | Value |
|---|---|
| m | 0.58 (17.2 um/px in the eye); search target 0.55, penalised only weakly |
| RMS spot, 9 fields | 4.0-9.7 um (centre field 9.6, edge 4.0-7.8) |
| Image extent | x 0.37-7.12 mm in the 9.6 mm half |
| Working f/# | about 22 (stop 6.25 mm): **~2.3x less light than the 138 mm design (f/14)** |
| MTF at 25 lp/mm | worst 0.12, mean 0.32 (diffraction cutoff lower at f/22) |

## Model-eye image simulation (`DESIGN=stock200_final python3 src/simulate_images.py`)
P1-P4 separation 118 px; gaze error 0.12 deg RMS (max 0.35) over +-15 deg, 0.044 deg inside +-12 deg; precision 0.015-0.018 deg;
eye depth +-1 mm -> 0.11-0.12 deg, +-2 mm -> 0.20-0.23 deg; lateral +-0.5 mm -> 0.05-0.07 deg.
The simulation keeps the P1 peak fixed at 9 ke-; at f/22 the real signal is ~2.3x lower for the same LED power, so raise LED power or exposure
(exposure limit 445 us at 2247 fps) and re-check P4 SNR.
