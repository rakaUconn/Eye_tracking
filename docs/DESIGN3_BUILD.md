# Design 3 (selected design): three-element stock objective, stop Ø12 mm, eye -> first lens 199 mm (long tube)

Elements: **LBF254-200 (reversed) + AC508-150-B (2 inch) + AC254-150**, all Thorlabs stock. Found by `src/search3.py` / `refine3.py`
(`results/design3_final.json`), simulated with `DESIGN=design3_final python3 src/simulate_images.py`
(`results/sim_*_design3_final.*`), layout in `results/design3_layout.png`.
Caveats as in the other documents: glass data typed from memory, crown/flint thickness splits of the doublets assumed, filter and cover glass are
placeholders (3 mm N-BK7, 1 mm N-BK7 + 0.5 mm gap), spacings are a local optimum, and nothing here has been checked in OpticStudio.

## 1. Prescription (one channel, unfolded; z = 0 at the stop; mm)
| # | Item | Radius | Thickness | Glass | Semi-diameter |
|---|---|---|---|---|---|
| OBJ | eye plane | inf | **196.005** | - | |
| 1 | CB | - | 0 | - | decenter X = -6.5 |
| 2 | STOP, Ø12 mm (radius 6.0) + filter | inf | 3.0 | N-BK7 proxy | |
| 3 | air | inf | **0.300** | - | |
| 4 | CB | - | 0 | - | decenter X = +6.5 (pick-up from 1, scale -1) |
| 5 | LBF254-200-A, **reversed** (catalogue R1/R2 = 121.5 / -684.5) | **+684.5** | 4.0 | N-BK7 | 11.43 |
| 6 | | **-121.5** | **112.536** | air | 11.43 |
| 7 | AC508-150-B, standard (catalogue 112.2 / -95.9 / -325.1) | +112.2 | 10.0 | N-LAK22 | 22.86 |
| 8 | | -95.9 | 3.2 | N-SF6HT | 22.86 |
| 9 | | -325.1 | **79.944** | air | 22.86 |
| 10 | AC254-150, standard (91.6 / -66.7 / -197.7) | +91.6 | 5.4 | N-BK7 | 11.43 |
| 11 | | -66.7 | 2.5 | SF5 | 11.43 |
| 12 | | -197.7 | **39.751** | air | 11.43 |
| 13 | cover glass | inf | 1.0 | N-BK7 proxy | |
| 14 | gap to die | inf | 0.5 | - | |
| IMA | sensor | | | | |

Filter front to sensor: 262.1 mm. Eye -> first lens = 196.005 + 3.0 + 0.3 = **199.3 mm**.
Folded: eye -> M1 30 mm, M1 -> V-prism 25.0 mm (IPD 63), V -> stop **141.0 mm** (30 + 25 + 141.0 = 196.0).
Stop holes Ø12 mm, 13.0 mm apart: a 1.0 mm web between them, so the V-prism knife edge must be sharp (ridge <= 0.3 mm) and aligned.

## 2. Predicted performance (840-860 nm, geometric, centroid reference)
| Item | Value |
|---|---|
| Magnification | 0.53 (18.9 um/px in the eye) |
| Image extent on the sensor half | x 0.35-6.51 mm |
| RMS spot, rows Y = -7.6 / 0 / +7.6, columns X = -12.3 / -6.5 / -0.7 (um) | 12.6 5.7 8.1 / 6.7 11.1 12.5 / 12.6 5.7 8.1 (mean 9.2, max 12.6) |
| MTF at 25 lp/mm (geometric x diffraction) | worst field 0.08, mean 0.44 |
| Working f/# | 10.2 (about 4.8x the light of the f/22 design) |
| Vignetting | 8% worst field (the 1-inch lenses clip some off-axis beams) |

## 3. Build steps
1. **Check in OpticStudio first.** Enter the table above (CB pairs as in `ZEMAX_BUILD_STEPS.md`; ray aiming Real; fields X = -6.5 +- 5.8 mm, Y = +-7.6 mm; wavelengths 0.84/0.85/0.86 um). Replace radii/thicknesses/glass by the vendor `.zmx` files; compare spots and magnification with section 2 (30% tolerance). Then re-optimise only the thicknesses: OBJ, surface 3, 6, 9, 12 (eye -> first lens limited to 195-205 mm).
2. **Mechanics.** The tube runs 262 mm from filter to sensor. Use SM1 for the two 1-inch lenses and SM2 for the AC508-150-B with an SM2-to-SM1 adapter at both ends, or a cage system of 60 mm cage rods; keep all three lens centres on one axis within +-0.1 mm, tilts < 0.1 deg. Lens spacing is set by spacer tubes, not by retaining rings (gaps 112.5 mm and 79.9 mm).
3. **Order of assembly:** stop + filter plate (stop on the filter front) -> 0.3 mm shim -> LBF254-200 (reversed: the flat-ish R 684.5 face toward the eye, the strongly curved face toward the camera) -> 112.5 mm spacer -> AC508-150-B (crown-glass first, standard orientation) -> 79.9 mm spacer -> AC254-150 (standard orientation) -> camera on a rail (about 39.8 mm from the last lens vertex to the cover glass).
4. **Stop plate:** two Ø12 mm holes at x = +-6.5 mm about the tube axis, on the plate that carries the filter; black anodised, knife-edge-thin septum between the holes.
5. **Periscope and V-prism:** as in `STOCK_LENS_BUILD_GUIDE.md` section 4 (M1 at 30 mm, V at 25 mm, V -> stop 141.0 mm); equal path lengths < 0.05 mm.
6. **Focus and calibration:** backlit grid target at the eye plane; adjust the camera rail until the 9-point grid is sharp (expect m = 0.53 +- 1%). Calibrate with the model eye as in the guide (5x5 grid, 2nd-order fit).
7. **Illumination:** the simulation assumes the LED power gives a P1 peak of about 60% of full scale and P4 at 1.2% of P1. At f/10 the signal is higher than at f/22, so reduce the LED power or exposure (keep exposure <= 445 us at 2247 fps) and verify P4 SNR on the real camera.
8. **IR safety** and the OpticStudio cross-talk/tolerancing steps are unchanged from the other guides and are still to be done.

## 4. Model-eye image simulation (noisy frames, left eye)
| Quantity | Result |
|---|---|
| P1-P4 separation, straight gaze | 108 px |
| Gaze error, 7x7 test grid +-15 deg | RMS 0.12 deg, max 0.35 deg |
| Gaze error inside +-12 deg | RMS 0.049 deg |
| Precision (200 noisy frames) | 0.015 deg (yaw), 0.014 deg (pitch) |
| Lateral eye shift +-0.5 mm | 0.05 deg (no effect) |
| P4 detection rate vs eye depth shift (moving away = +) | -2 mm to 0: 100%; +0.5 mm: 93%; +1 mm: **59%**; +2 mm: 78% |
| Gaze error vs depth, detected frames | -2 mm: 0.20 deg, -1 mm: 0.10 deg, 0: 0.05 deg, +2 mm: 0.27 deg (the +1 mm run contained mis-detections, 21 deg RMS, before excluding missed P4 frames) |

The shallower depth of field at f/10 makes P4 (1.2% of P1) too weak and too blurred when the eye moves **away** from the camera by about 1 mm; the 22 f/# design
detected P4 at every depth shift tested (100% from -2 to +2 mm). Remedy (tested below): bias the focus about 0.5 mm of eye depth toward the camera-far side, or use a longer exposure with a saturated P1, or hold the head within about -2/+0.5 mm of nominal.
**Focus-bias test (simulated, `FOCUS_BIAS` in `src/simulate_images.py`, `src/detect_vs_depth.py`):** focusing on a plane 0.5 mm of eye depth farther from the camera than the P1/P4 mean raises the P4 detection rate to **100% for eye depth shifts from -2 mm to +1 mm** (+2 mm: 44%); a 1.0 mm bias gives the same -2 to +1 mm range but with a 0.86 px P4 centroid error at -2 mm. Use a bias of about 0.5 mm (move the camera about m^2 x 0.5 = 0.14 mm from the best-focus position of the straight-gaze P1/P4 midpoint), then confirm on the real camera.
These detection numbers come from one noise model and 27 frames per depth value; treat them as indicative.
