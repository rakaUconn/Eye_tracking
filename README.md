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

## Stock-lens swap (Thorlabs list, 272 single/pair configurations, `src/stock.py`, `opt_stock.py`, `refine_stock.py`, `fixLo.py`)
Catalogue radii/glasses reproduce catalogue EFL within 1% (Sellmeier data from memory; doublet crown/flint thickness split assumed).
Best stock option: **AC254-150 (reversed, N-BK7/SF5) + AC254-075-B**, touching (gap 0.05 mm), stop at the first lens, eye->lens **137.3 mm**, sensor 69.2 mm behind the filter/cover stack.
| | stock pair | surrogate |
|---|---|---|
| m | 0.55 | 0.55 |
| RMS spot | 5.5-16.2 um (mean ~12) | 4.1-8.9 um |
| MTF@25 lp/mm | min 0.12, mean 0.28 | min 0.31 |
| Image x range | 0.36-6.79 mm | 0.36-6.77 mm |
At the requested 149.4 mm the same pairs only reach m ~ 0.49-0.50 (RMS 5-22 um) because the focal length is too long.
Stock lenses do **not** meet the 0.40 MTF target; only the best-placed ~half of the field is near one pixel.

## Stock-lens build guide
See `docs/STOCK_LENS_BUILD_GUIDE.md` (final stock design, step-by-step build, model-eye image simulation and analysis; `src/stock_final.py`, `src/simulate_images.py`, `results/sim_*.png`).

OpticStudio walkthrough: `docs/ZEMAX_BUILD_STEPS.md`.

200 mm variant: `docs/STOCK_200MM_DESIGN.md`.

Stop-diameter / 2-inch study: `docs/STOP_DIAMETER_STUDY.md`.

Design 3 (3-element stock objective, long tube): `docs/DESIGN3_BUILD.md`.

Relay (f150 + f75) check: `docs/RELAY_150_75.md`.

**Selected design: Design 3** (`docs/DESIGN3_BUILD.md`). The relay of `docs/RELAY_150_75.md` was evaluated and rejected.
