# Single-sensor binocular eye-tracking optics (Lux19HS, 850 nm)

Sensor split left/right (2 x 9.6 x 10.8 mm halves, 10 um px), head fixed, m = 0.55.
Everything here is an in-house ray-trace study (no OpticStudio available); lenses are **surrogate** doublets, not catalogue parts.

- `src/raytrace.py` sequential 3-D tracer + Sellmeier glasses; `src/channel.py`, `src/opt2.py` one-channel model + optimiser
- `src/eye.py` Navarro eye, P1/P4 vs gaze; `src/analyze.py` produces `results/`
- `results/summary.json`, `spots.png`, `mtf.png`, `doublet_opt.json` (single doublet: not good enough, ~9-18 um rms)

## Design (two f~100 mm-class cemented doublets, N-BK7/F2, off-axis chief ray 6.5 mm)
| | |
|---|---|
| Eye field / magnification | 11.6 x 15.2 mm, m = 0.550 (18.2 um/px) |
| Eye -> stop (unfolded) | 149.0 mm, stop O6.25 mm, hole offset +-6.5 mm |
| Image centres / edges | +-3.54 mm; inner 0.36, outer 6.77 mm (half = 9.6) |
| Working f/# | ~15.5 (NA 0.032), diffraction cutoff 76 lp/mm |
| RMS spot (840-860 nm) | 4.1-8.9 um, all 9 fields |
| MTF @25 lp/mm | 0.31 (worst corner) .. ~0.57; diffraction limit 0.59 |
| Defocus +-1 mm eye depth | ~16 um rms (<2 px); P1/P4 shift together |
| IPD 54-74 mm (path +-5 mm) | refocus +-1.5 mm at the sensor, m 0.525-0.576, still on sensor |
| Folded layout | eye->M1 30, M1->V 25 (20.5-30.5 over IPD range), V->stop 94 mm |
| P1/P4 | depth difference ~0.3 mm; P1-P4 slope ~0.11-0.12 mm/deg in eye space (~0.06 mm/deg on sensor) |

## Open items
1. Replace surrogate doublets with catalogue lenses (needs vendor Zemax files; no internet here).
2. Corner MTF 0.31 < 0.40 target; lateral colour dominates -> use the narrow FBH850-10 band.
3. Cover-glass/filter thicknesses are placeholders (3 mm / 1 mm).
4. Non-sequential cross-talk, tolerancing (Monte Carlo) and IR safety still to do.
