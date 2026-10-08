# Build the stock-lens binocular eye tracker in Zemax OpticStudio

Design: AC254-150-B (reversed) + AC254-075-B, m = 0.55, Lux19HS split sensor, 850 nm.
Menu names follow OpticStudio 2023-24 from memory and are marked **(verify)** where I am not sure.
All reference numbers below come from my Python tracer (`src/stock_final.py`); use them as checkpoints, not as truth.
Companion file: `Zemax_build_guide.md` (your original guide, Parts A-F); this file replaces its Part B table and numbers.

## 0. Before you start
1. From each Thorlabs part page, download the Zemax file (`.zmx`/`.zar`) for **AC254-150-B** and **AC254-075-B**. Use them to check or replace the radii/glass in step 1.2.
2. Collect the filter datasheet (thickness, substrate) and the Lux19HS cover-glass thickness/material. Placeholders used below: filter 3.0 mm N-BK7, cover glass 1.0 mm N-BK7, 0.5 mm gap to the die.
3. Create three files: `A_eye.zmx`, `B_objective.zmx`, `C_folded.zmx`.

## 1. Part B first: the objective (one channel, unfolded)

### 1.1 System Explorer
| Setting | Value |
|---|---|
| Units | mm |
| Aperture type | **Float By Stop Size** |
| Ray aiming | **Real** (needed because the stop is off the lens axis) **(verify: System Explorer, Ray Aiming)** |
| Wavelengths | 0.84, 0.85, 0.86 um, weight 1, primary 0.85 |
| Field type | **Object Height** |
| Fields (X, Y mm) | the 3x3 grid: X in {-12.3, -6.5, -0.7}, Y in {-7.6, 0, +7.6} |

The object is the eye plane; X = -6.5 is the eye centre in the lens-axis frame and +-5.8 is the half field (eye field 11.6 x 15.2 mm).

### 1.2 Lens Data Editor
Enter these rows. "CB" = Coordinate Break (Surface Type = Coordinate Break).

| # | Type | Radius | Thickness | Glass | Semi-diameter / note |
|---|---|---|---|---|---|
| OBJ | Standard | inf | **134.84** | - | to the stop; make variable later (130-150) |
| 1 | CB | - | 0 | - | **Decenter X = -6.5** |
| 2 | Standard, **STOP** | inf | 3.0 | N-BK7 (filter proxy) | circular aperture, **max radius 3.125** (diameter 6.25) |
| 3 | Standard | inf | **0.498** | - | air; variable, >= 0.3 |
| 4 | CB | - | 0 | - | **Decenter X = +6.5**, pick-up from surface 1, scale -1 |
| 5 | Standard | **+197.7** | 2.5 | SF5 | SD 11.43 (AC254-150 reversed: flint face toward the eye) |
| 6 | Standard | **+66.7** | 5.4 | N-BK7 | SD 11.43 |
| 7 | Standard | **-91.6** | **0.30** | - | SD 11.43; gap to lens B, variable, >= 0.3 |
| 8 | Standard | **+36.90** | 4.5 | N-BAF10 | SD 11.43 (AC254-075-B, standard orientation) |
| 9 | Standard | **-42.17** | 2.1 | N-SF6HT | SD 11.43 |
| 10 | Standard | **+417.8** | **71.13** | - | SD 11.43; lens B to cover glass, **variable** |
| 11 | Standard | inf | 1.0 | N-BK7 | cover glass (placeholder) |
| 12 | Standard | inf | 0.5 | - | gap to the die |
| IMA | Standard | inf | - | - | sensor |

Notes
* The reversal: Thorlabs lists AC254-150 as R1/R2/R3 = 91.6 / -66.7 / -197.7 (N-BK7 then SF5). Reversed, light meets the -197.7 face first, so the signs flip (+197.7, +66.7, -91.6) and the glass order swaps.
* The crown/flint thickness split of both doublets (5.4/2.5 and 4.5/2.1) is my assumption. Replace it with the values in the vendor `.zmx`, or insert the vendor lens from the lens catalogue **(verify)** and flip the AC254-150 with Tools, Miscellaneous, Reverse Elements **(verify)**.
* The CB pair puts the stop at x = -6.5 mm (on the eye's chief ray) while the lens stays on its own axis. The 6.5 mm off-axis path is what the design relies on.

### 1.3 First check, then optimise
1. 2D and 3D Layout: rays enter at x about -6.5, cross lens A off-axis, cross the axis and reach the sensor on the +x side.
2. Footprint diagram on surfaces 5-10 **(verify name)**: no vignetting, footprints inside SD 11.43.
3. Merit Function Editor: Optimization Wizard, RMS, Spot Radius, Centroid, rectangular pupil array (8x8 or 6 rings), axial symmetry off. Add rows:
   * `REAX` at field (X=-12.3, Y=0) target **+6.79 mm**; at (X=-0.7, Y=0) target **+0.36 mm**; at (-6.5, 0) target about **+3.54 mm**. These fix m = 0.55 and the margin to the centre line.
   * Thickness limits: surface 3 >= 0.3 and surface 7 >= 0.3 (e.g. `MNCG`/`TTHI`-based operands).
4. Variables: OBJ thickness (130-150), surface 3, surface 7, surface 10 thicknesses. **Do not** vary radii or glass (stock parts).
5. Run Optimize (Damped Least Squares), then Hammer for a few minutes.

### 1.4 Expected results (my tracer, 840-860 nm, centroid, geometric)
| Item | Expected |
|---|---|
| OBJ thickness after optimisation | about 134.8 mm |
| Surface 3 / surface 7 | about 0.5 mm / 0.3 mm (at the limits) |
| Surface 10 (lens B to cover) | about 71.1 mm |
| m | 0.55 (REAX range 0.36-6.79 mm over the 11.6 mm field) |
| MTF at 25 lp/mm, worst field | about 0.12 (geometric x diffraction); diffraction limit 0.62; mean over fields about 0.28 |

RMS spot radius in um (rows Y = -7.6 / 0 / +7.6, columns X = -12.3 / -6.5 / -0.7):

| | X -12.3 | X -6.5 | X -0.7 |
|---|---|---|---|
| Y -7.6 | 15.7 | 12.0 | 16.6 |
| Y 0 | 9.5 | 16.6 | 6.3 |
| Y +7.6 | 15.7 | 12.0 | 16.6 |

If your values are more than about 30% off, check in this order: CB sign pairing (pick-up scale -1), ray aiming = Real, the reversal of AC254-150, glass catalogue differences.

### 1.5 Analyses to run and save
* Spot diagram (reference centroid, Airy disc and a 10 um pixel box overlaid).
* FFT MTF at 25 and 50 lp/mm, all fields, pupil sampling 64x64.
* Huygens PSF at the centre field **(verify)**; encircled energy inside 1 pixel.
* Depth of field: Multi-Configuration Editor, OBJ thickness = 134.84 +- {1, 2} mm. Expect about 15 um RMS at +-1 mm.
* IPD sweep: OBJ thickness 134.84 +- 5 mm (what IPD 54/74 mm does to the path); refocus with surface 10. Expect refocus about +-1.5 mm and m about 0.525-0.576.

## 2. Part C: folded model (layout and path audit)
1. Save `B_objective.zmx` as `C_folded.zmx`. Change the OBJ thickness to 30 mm and add, in the x = -6.5 mm frame of the left channel:
   * fold mirror M1 at 45 degrees (Tools, Design, Add Fold Mirror **(verify)**), 30 mm from the eye;
   * fold mirror V-face at 45 degrees, **25.0 mm** after M1 (= IPD/2 - 6.5);
   * the stop's CB frame **79.84 mm** after the V face. Check: 30 + 25.0 + 79.84 = 134.84.
2. In the 3D Layout confirm the beam leaves the V face at x = -6.5 mm, parallel to the lens axis.
3. Right channel: Multi-Configuration Editor, config 2 flips the signs of the M1/V fold tilts and of both CB decenters (+6.5 / -6.5). The field list stays the same.
4. Equivalence test: folded and unfolded spot diagrams must agree, apart from mirror parity.
5. Path audit: optical path length operand (`OPTH`, **verify**) for both channel configs; difference **< 0.01 mm** at IPD 63. Then move M1 in x for IPD 54-74 mm (M1 to V face 20.5-30.5 mm) and refocus with surface 10.
6. Rhomboid option: replace M1 + V by two N-BK7 rhomboid blocks with TIR faces; check the internal incidence angle (45 +- 2 degrees) against the 41.5 degree critical angle at 850 nm.

## 3. Part A: the model eye (Navarro) and Purkinje images
Follow `Zemax_build_guide.md` Part A with these changes:
1. Surface table (Navarro 1999, **verify** against the paper): cornea R 7.72, k -0.26, t 0.55; aqueous R 6.50, t 3.05; lens front R 10.2, k -3.1316, t 4.0 (STOP, 4 mm pupil); lens back R -6.0, k -1.0, t 16.3203; retina R -12.0.
2. Indices: first run at 0.555 um (1.376, 1.336, 1.42, 1.336), then repeat at 0.85 um. My tracer used 1.3718, 1.3331, 1.4130, 1.3331 at 850 nm, which is an approximation. **Verify** with the Navarro dispersion formula.
3. P1: surface 1 = MIRROR. P4: surface 4 = MIRROR, retrace back with pick-ups (Radius -1, Conic +1, Thickness -1), glass off by one after the mirror.
4. Source: collimated, 17 degrees from the camera axis (mirrored for the other eye); rotate the eye about the centre of rotation, 13.5 mm behind the apex.
5. Checkpoints from `src/eye.py` (straight gaze): P4 is about 0.33 mm deeper than P1; **P1-P4 lateral separation 2.03 mm** in the eye (112 px at m = 0.55, 10 um pixels); slope about **0.11 mm per degree**. Both glints shift together with eye depth.
6. Tabulate P1, P4 and P1-P4 against gaze (-15 to +15 degrees, horizontal and vertical) and compare with `results/sim_summary.json`.

## 4. Join eye and objective for image simulation
1. Simplest approach, as used in the Python simulation: treat each Purkinje image as a point object at its virtual position (x, y, depth). Use object-height fields for the lateral position and OBJ thickness changes for the depth offset (P4 about +0.33 mm from P1; focus at their mean).
2. Analysis, Image Quality, **Image Simulation (verify)**: source bitmap with two bright points (P1) and two points at 1.2% intensity (P4); FFT with PSF, pixel size 10 um, wavelength 0.85 um. Compare blur and separation (112 px) with `results/sim_frames.png`.
3. Export the simulated image and run it through `detect`, `feature` and `design_matrix` in `src/simulate_images.py`. Expect about 0.1 degrees RMS gaze error (0.05 inside +-12 degrees).
4. For true ray paths through the eye, build the eye in Non-Sequential mode **(verify)** and detect the glints on a detector at the sensor plane.

## 5. Parts D and E: cross-talk and tolerancing
* **Cross-talk (NSC)**: rebuild the folded model in Non-Sequential mode **(verify)**: source rectangles 11.6 x 15.2 mm per eye, wide cone (+-15-20 degrees), 850 nm; MIRROR objects for M1 and V; absorbing stop plate and septum; two detector rectangles (one per sensor half, 960 x 1080 pixels). Run left-only and right-only; require flux on the other half / total **< 1e-4**.
* **Tolerancing**: vendor tolerances (EFL +-1%, thickness +-0.1 mm, centering per datasheet) plus assembly (mirror tilt, V position, stop decenter, sensor decenter/tilt). Compensators: surface 10 (focus) and sensor decenter. Monte Carlo, 200 trials. Target 80% of trials with RMS spot <= 20 um. The nominal worst field is already about 17 um, so expect little margin.

## 6. Acceptance checklist
| Item | Target for this stock design |
|---|---|
| RMS spot, all fields | <= 17 um (the custom surrogate design reached <= 9 um) |
| m and image extent | 0.55; x 0.36-6.79 mm |
| Vignetting | none (footprints inside SD 11.43) |
| Path-length difference between channels | < 0.01 mm |
| P1-P4 separation | 2.03 mm in the eye (112 px) |
| Cross-talk | < 1e-4 |
| Image-simulation gaze error | about 0.1 degrees RMS |
