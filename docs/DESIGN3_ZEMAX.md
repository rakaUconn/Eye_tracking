# OpticStudio walkthrough for Design 3 (LBF254-200 reversed + AC508-150-B + AC254-150, stop Ø12 mm)

Companion to `DESIGN3_BUILD.md` (prescription and mechanics) and `Zemax_build_guide.md` (eye model, cross-talk, tolerancing).
Menu names are from memory of OpticStudio 2023-24 and marked **(verify)** where unsure. Every number marked "expected" comes from my own Python
tracer, not from OpticStudio, so allow about 30% difference on spot sizes at first and treat a larger gap as a transcription error to hunt down.

## 0. Preparation
1. Download the Zemax files (`.zmx`/`.zar`) for **LBF254-200-A**, **AC508-150-B** and **AC254-150-B** from the Thorlabs part pages. Keep them for step 2.4 (radii, thicknesses, glass).
2. Make a project folder with `D3_objective.zmx` (steps 1-4), `D3_folded.zmx` (step 5), `D3_eye.zmx` (step 7).
3. Glass names you need: N-BK7, SF5, N-LAK22, N-SF6HT. If the catalogue has `SF5` only as `N-SF5`, check which one the vendor file uses. I used Schott SF5.

## 1. System Explorer
| Setting | Value |
|---|---|
| Units | mm |
| Aperture | **Float By Stop Size** |
| Ray aiming | **Real** **(verify path: System Explorer, Ray Aiming)** |
| Wavelengths | 0.84, 0.85, 0.86 um, weight 1, primary 0.85 |
| Field type | **Object Height**, in mm |
| Fields (X, Y) | X in {-12.3, -6.5, -0.7} x Y in {-7.6, 0, +7.6}: nine fields |

X = -6.5 mm is the eye centre in the lens-axis frame; +-5.8 mm is the half eye field. (Eye field 11.6 x 15.2 mm.)

## 2. Lens Data Editor

### 2.1 Surface table (enter exactly)
| # | Type | Radius | Thickness | Material | Semi-diameter | Comment |
|---|---|---|---|---|---|---|
| OBJ | Standard | inf | **196.005** | | | eye plane to stop |
| 1 | Coordinate Break | | 0 | | | **Decenter X = -6.5** |
| 2 | Standard (**STOP**) | inf | 3.0 | N-BK7 | circular aperture, **max radius 6.0** | stop on the front of the filter (proxy) |
| 3 | Standard | inf | **0.300** | | 14 | air |
| 4 | Coordinate Break | | 0 | | | **Decenter X = +6.5**; pick-up from surface 1, scale -1 |
| 5 | Standard | **+684.5** | 4.0 | N-BK7 | 11.43 | LBF254-200, reversed |
| 6 | Standard | **-121.5** | **112.536** | | 11.43 | |
| 7 | Standard | **+112.2** | 10.0 | N-LAK22 | 22.86 | AC508-150-B |
| 8 | Standard | **-95.9** | 3.2 | N-SF6HT | 22.86 | |
| 9 | Standard | **-325.1** | **79.944** | | 22.86 | |
| 10 | Standard | **+91.6** | 5.4 | N-BK7 | 11.43 | AC254-150 |
| 11 | Standard | **-66.7** | 2.5 | SF5 | 11.43 | |
| 12 | Standard | **-197.7** | **39.751** | | 11.43 | to cover glass |
| 13 | Standard | inf | 1.0 | N-BK7 | 14 | sensor cover glass (placeholder) |
| 14 | Standard | inf | 0.5 | | 14 | gap to the die |
| IMA | Standard | inf | | | | sensor |

Semi-diameters 11.43 = 90% of the 25.4 mm clear aperture; 22.86 for the 50.8 mm lens. Set them as **Fixed** (not Automatic) so that real vignetting shows.

### 2.2 Notes on the table
* **Reversal of LBF254-200**: catalogue R1/R2 = +121.5 / -684.5 (strong curve first); mounted reversed the nearly flat face meets the light first, hence +684.5 then -121.5. The other two lenses are standard orientation.
* **AC508-150-B and AC254-150**: catalogue R1/R2/R3 = 112.2/-95.9/-325.1 and 91.6/-66.7/-197.7. The crown/flint thickness splits (10.0/3.2 and 5.4/2.5) are my assumptions: replace with the vendor values.
* **Decenter pair**: surfaces 1 and 4 put the stop (surface 2) 6.5 mm off the lens axis on the eye's chief ray, while all lenses stay centred on the axis. Check the pick-up in the editor (Solve type: Pick up, surface 1, column Decenter X, scale factor -1).
* The filter is modelled as 3 mm N-BK7 in front of the stop; use the real filter thickness/substrate later.

### 2.3 First look
1. Layout -> 3D layout and Cross-section (XZ): the beam enters at x about -6.5, passes through the first lens off-axis, crosses the axis in the long gap, passes through the 2-inch lens, then the last lens and lands on the +x side of the sensor.
2. **Footprint diagram** on surfaces 5-12 **(verify name)**: report which surface clips rays. My tracer expects about 8% of the worst field lost; the candidates are the two 1-inch lenses at the far ends of the tube.
3. Spot diagram (Analysis -> Spot Diagram -> Standard), reference **Centroid**; show the Airy disc.

### 2.4 Compare with the vendor files
Open each vendor `.zmx`, copy its lens rows into a scratch file and compare radii, thicknesses and glass with 2.1. Update 2.1 if they differ: crown/flint splits especially. Keep the spacings (thicknesses of surfaces 3, 6, 9, 12) and re-optimise them in step 3.

## 3. Optimisation (thicknesses only)
1. Merit Function Editor -> Optimization Wizard: Image Quality **RMS**, **Spot Radius**, **Centroid**, pupil integration **Rectangular Array** 8 x 8 (or 6 rings), **Assume Axial Symmetry off**, tick **Ignore lateral color off**. Delete default thickness constraints.
2. Variables (V on the thickness column): **OBJ**, surface 3, 6, 9, 12. **Do not vary radii or glass.**
3. Constraints (add rows with `MNCT`/`MXCT` or `OPGT`/`OPLT` **(verify operand names)**):
   * surface 3 >= 0.3 mm; surfaces 6, 9 >= 1 mm; OBJ between 150 and 215 mm;
   * eye -> first lens: **OBJ + 3.0 + surface 3 between 195 and 205 mm** (build this as a sum with `SUMM` or `OSUM` **(verify)**; enforce with `OPGT`/`OPLT`);
   * surface 12 >= 8 mm.
4. Image-position operands (these hold the magnification and keep both eye images off the centre line): `REAX` targets, at Hx = -1, Hy = 0 (X = -12.3 mm): **+6.51 mm**; at Hx = +1, Hy = 0 (X = -0.7 mm): **+0.35 mm**; at Hx = 0, Hy = 0 about **+3.43 mm**. Weight 1 each, relative to the RMS spot rows. (Sign: the image is inverted, hence positive x on the sensor.)
5. Run Optimize (DLS), then Hammer 5-10 minutes; finish with DLS again.

## 4. Expected result (my tracer; OpticStudio should land close)
| Quantity | Expected |
|---|---|
| OBJ thickness | about 196.0 mm (eye -> stop) |
| Surface 3 / 6 / 9 / 12 | 0.30 / 112.5 / 79.9 / 39.75 mm |
| Eye -> first lens | 199.3 mm |
| Magnification | 0.53 (x range on the sensor 0.35-6.51 mm) |
| Working f/# | about 10.2 |

RMS spot radius (um); rows Y = -7.6 / 0 / +7.6, columns X = -12.3 / -6.5 / -0.7:

| | X -12.3 | X -6.5 | X -0.7 |
|---|---|---|---|
| Y -7.6 | 12.6 | 5.7 | 8.1 |
| Y 0 | 6.7 | 11.1 | 12.5 |
| Y +7.6 | 12.6 | 5.7 | 8.1 |

FFT MTF at 25 lp/mm: worst field about 0.08, mean about 0.44 (geometric x diffraction in my tracer; OpticStudio's FFT MTF will include diffraction exactly, so compare the mean first).
If your numbers are far off, check in this order: the sign pairing of the decenter surfaces; ray aiming Real; the LBF254-200 reversal; semi-diameters Fixed (not automatic); the thicknesses in 2.1.

## 5. Analyses to run and save
* Spot diagram and FFT MTF at all nine fields (pupil sampling 64 x 64; MTF at 25 and 50 lp/mm).
* **Huygens PSF** at the centre field; encircled energy inside 10 um (one pixel).
* **Depth of field and focus bias**: Multi-Configuration Editor, configs with OBJ = 196.005 + dz for dz in {-2, -1, 0, +0.5, +1, +2} mm. In my simulation the P4 detection works for eye depth -2 to +1 mm when the focus is biased 0.5 mm toward the far side (see `DESIGN3_BUILD.md`); with this multi-config, look for an OBJ offset that makes the RMS spot at dz = -2 and +1 mm similar, and adopt that as the nominal focus. Refocus is done by the lens-to-sensor thickness (surface 12): to move the best focus plane by 0.5 mm in eye space shift surface 12 by about m^2 x 0.5 = 0.14 mm.
* **IPD sweep**: configs with OBJ = 196.005 +- 5 mm (what IPD 54/74 mm does to the path length). Refocus with surface 12; record m, RMS and image x range.
* **Footprints** on each lens for all fields, to quantify the vignetting.

## 6. Folded model (periscope)
1. Save as `D3_folded.zmx`. Change OBJ thickness to **30.0** (eye -> M1) and add before surface 1 (in the eye frame):
   * fold mirror M1 at 45 degrees (Tools -> Design -> Add Fold Mirror **(verify)**, or Coordinate Break with tilt 45 degrees about Y followed by a Mirror surface); 30 mm from the eye;
   * fold mirror V-face at 45 degrees, **25.0 mm** after M1 (= IPD/2 - 6.5 at IPD 63 mm);
   * then **141.005 mm** from the V face to the stop CB frame (30 + 25.0 + 141.005 = 196.005).
2. In the 3D layout confirm the beam leaves the V face at x = -6.5 mm parallel to the lens axis.
3. Right channel: Multi-Configuration Editor, config 2 flips the signs of the M1/V tilts and of both CB decenters (+6.5 / -6.5). Keep the field list.
4. Equivalence: spot diagrams of the folded model must equal the unfolded ones (up to mirror parity).
5. Path audit: optical path length (`OPTH` **verify**) for both configs; difference **< 0.01 mm** at IPD 63. Then vary IPD 54-74 mm (M1 -> V 20.5-30.5 mm) and refocus with surface 12.
6. The V-prism knife edge is 1.0 mm wide in the holes' web (holes Ø12 mm, 13 mm apart); model the ridge as a 0.3 mm opaque strip in the non-sequential model of step 8.

## 7. Eye model and Purkinje images
Follow `Zemax_build_guide.md` Part A with: Navarro surfaces (cornea R 7.72 k -0.26 t 0.55; aqueous R 6.50 t 3.05; lens front R 10.2 k -3.1316 t 4.0 STOP 4 mm; lens back R -6.0 k -1.0 t 16.3203; retina R -12.0) **(verify against the paper)**; indices at 0.85 um 1.3718 / 1.3331 / 1.4130 / 1.3331 (my approximation, **verify**); source 17 degrees off the camera axis, mirrored for the second eye; rotation centre 13.5 mm behind the apex.
Checkpoints at straight gaze: P4 about 0.33 mm deeper than P1; **P1-P4 separation 2.03 mm in the eye, 108 px on the sensor with Design 3 (m = 0.53)**; slope about 0.11 mm per degree of eye rotation.
Image simulation: use each glint as a point object (object heights from the eye model, depth offset through OBJ thickness; P4 about +0.33 mm from P1 with the **0.5 mm focus bias** applied). Analysis -> Image Quality -> **Image Simulation (verify)**: two P1 points at full intensity, two P4 points at 1.2% of P1; FFT with PSF, 10 um pixel, 0.85 um. Compare with `results/sim_frames_design3_final.png`.

## 8. Cross-talk (non-sequential)
Rebuild the folded model in Non-Sequential mode **(verify: File -> New, Mode Non-Sequential, or the Convert to NSC tool)**: source rectangles 11.6 x 15.2 mm for each eye, wide cone +-15-20 degrees, 850 nm; M1 and V-prism faces as MIRROR objects (the knife-edge ridge as an absorbing strip 0.3 mm wide); the stop plate with two Ø12 mm holes at x = +-6.5 mm (ABSORB); lens barrel/spacer tubes absorbing; two detector rectangles (left half, right half, 960 x 1080 pixels, 10 um). Left-only then right-only runs: **flux on the other half / total < 1e-4**. The 1.0 mm web between the holes and the 262 mm tube make stray light entry through the open tube a risk: add baffles in the long gaps.

## 9. Tolerancing
Vendor tolerances (EFL +-1%, thickness +-0.1 mm, centering per datasheet), assembly tolerances (mirror tilt, V position, stop decenter, tube tilt, sensor decenter/tilt). Compensators: surface 12 (focus) and sensor decenter. 200 Monte Carlo trials. Target: 80% of trials with RMS spot <= 15 um (nominal worst field is 12.6 um, so margin is small).

## 10. Acceptance checklist
| Item | Target |
|---|---|
| RMS spot, all fields | <= 13 um nominal (my tracer: 12.6 max, 9.2 mean) |
| Magnification / image extent | 0.53 / x 0.35-6.51 mm |
| Vignetting | <= 8% worst field, no clipping at the stop |
| Eye -> first lens | 195-205 mm |
| Path-length difference between channels | < 0.01 mm |
| P1-P4 separation | 2.03 mm in the eye, about 108 px |
| P4 detection vs depth | 100% for -2 to +1 mm with the 0.5 mm focus bias (simulation) |
| Cross-talk | < 1e-4 |
| Monte Carlo (80%) | RMS spot <= 15 um |
