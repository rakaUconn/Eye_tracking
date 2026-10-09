# OpticStudio walkthrough for Design 4A (LB1199 + AC508-150-B + LF1988 reversed + AC254-075-B, stop Ø14.7 mm)

Companion to `WIDE_STOCK_SEARCH.md` (how 4A was found, performance, build notes), `DESIGN3_ZEMAX.md` (same procedure for Design 3)
and `Zemax_build_guide.md` (eye model, cross-talk, tolerancing).
Menu and operand names are from OpticStudio 2023–24 and are marked **(verify)** where I am not sure of the exact name or path.
Every "expected" number comes from the in-house Python tracer (`src/fastchan.py`), not from OpticStudio. Allow about 30 % on spot
sizes at first; a larger gap almost always means a transcription error (see the checklist in step 4.3).

---------------------------------------------------------------------------------------------------------------------------------

## 0. Preparation

1. From the Thorlabs part pages download the Zemax files (`.zmx` / `.zar`) of
   **LB1199**, **AC508-150-B**, **LF1988-A** and **AC254-075-B**. You need them in step 2.5.
2. Make a project folder with three files:
   * `D4A_objective.zmx`: unfolded one-channel model (steps 1–5),
   * `D4A_folded.zmx`: periscope + V-prism, both channels (step 6),
   * `D4A_eye.zmx`: Navarro eye and Purkinje images (step 7).
3. Glasses used: **N-BK7, N-LAK22, N-SF6HT, N-BAF10** (all in the SCHOTT catalogue). Make sure SCHOTT is loaded:
   System Explorer → Material Catalogs → add SCHOTT.
4. Geometry in one sentence: one lens train on the z-axis; each eye looks through its own hole in a two-hole stop plate. The holes
   are **Ø14.72 mm, centred at x = ±7.661 mm**; the eye's field centre sits on the same line (x = −7.661 mm for the left eye in the
   unfolded model). After the lenses the left eye lands on the +x half of the sensor, the right eye on the −x half.

---------------------------------------------------------------------------------------------------------------------------------

## 1. System Explorer

| Setting | Value | Where |
|---|---|---|
| Lens units | mm | System Explorer → Units |
| Aperture type | **Float By Stop Size** | System Explorer → Aperture |
| Ray aiming | **Real** (keep "Use Enhanced Ray Aiming" if offered) | System Explorer → Aperture → Ray Aiming **(verify)** |
| Wavelengths | 0.840, **0.850 (primary)**, 0.860 µm, weights 1 / 1 / 1 | System Explorer → Wavelengths |
| Field type | **Object Height**, mm | System Explorer → Fields |
| Field normalization | Radial | System Explorer → Fields |

### 1.1 Fields (nine; X is in the lens-axis frame)

| Field | X (mm) | Y (mm) | Meaning |
|---|---|---|---|
| 1 | −13.461 | −7.6 | outer-bottom corner of the eye field |
| 2 | −7.661 | −7.6 | |
| 3 | −1.861 | −7.6 | inner-bottom corner (next to the centre line) |
| 4 | −13.461 | 0 | |
| 5 | **−7.661** | **0** | eye-field centre |
| 6 | −1.861 | 0 | |
| 7 | −13.461 | +7.6 | |
| 8 | −7.661 | +7.6 | |
| 9 | −1.861 | +7.6 | |

−7.661 mm is the hole centre; ±5.8 mm is half the 11.6 mm eye-field width, ±7.6 mm half the 15.2 mm height.
The largest radial field is √(13.461² + 7.6²) = **15.458 mm**: normalised field coordinates (Hx, Hy) used by operands later are
X / 15.458 and Y / 15.458.

---------------------------------------------------------------------------------------------------------------------------------

## 2. Lens Data Editor

### 2.1 Surface table (enter exactly)

| # | Type | Radius | Thickness | Material | Semi-diameter | Comment |
|---|---|---|---|---|---|---|
| OBJ | Standard | inf | **171.759** | | | eye (P1/P4 mid-plane) → stop |
| 1 | Coordinate Break | | 0 | | | **Decenter X = −7.661** |
| 2 | Standard (**STOP**) | inf | 3.000 | N-BK7 | aperture: circular, **max radius 7.361** | stop on the filter front (filter proxy) |
| 3 | Standard | inf | **0.796** | | 16 | air |
| 4 | Coordinate Break | | 0 | | | **Decenter X = +7.661** (pick-up of surf 1, scale −1) |
| 5 | Standard | **+205.000** | 6.200 | N-BK7 | 22.86 | LB1199 (bi-convex, symmetric) |
| 6 | Standard | **−205.000** | **0.500** | | 22.86 | air, vertex to vertex |
| 7 | Standard | **+112.200** | 10.000 | N-LAK22 | 22.86 | AC508-150-B, standard orientation |
| 8 | Standard | **−95.900** | 3.200 | N-SF6HT | 22.86 | |
| 9 | Standard | **−325.100** | **23.912** | | 22.86 | air |
| 10 | Standard | **−126.300** | 3.000 | N-BK7 | 11.43 | LF1988-A, **reversed** |
| 11 | Standard | **−250.000** | **88.855** | | 11.43 | air |
| 12 | Standard | **+36.900** | 4.500 | N-BAF10 | 11.43 | AC254-075-B, standard orientation |
| 13 | Standard | **−42.170** | 2.100 | N-SF6HT | 11.43 | |
| 14 | Standard | **+417.800** | **37.216** | | 11.43 | to the cover glass |
| 15 | Standard | inf | 1.000 | N-BK7 | 14 | sensor cover glass (placeholder) |
| 16 | Standard | inf | 0.500 | | 14 | gap to the die (placeholder) |
| IMA | Standard | inf | | | | sensor |

Totals to check (Reports → System Data / Prescription Data):

* eye → first lens vertex = 171.759 + 3.000 + 0.796 = **175.555 mm**
* stop → sensor = **184.779 mm**; eye → sensor = **356.538 mm**
* effective focal length of surfaces 5–14 (EFFL) about **154 mm (verify)**

### 2.2 How to enter it, click by click

1. **Coordinate breaks.** Insert surface 1, set Surface Type = Coordinate Break, Decenter X = −7.661.
   Insert surface 4 as a Coordinate Break; on its Decenter X cell open the Solve dialog → **Pickup**, From Surface 1,
   Scale Factor −1, Offset 0. The stop (surface 2) now sits on the left-eye hole while every lens stays on the axis.
2. **Stop aperture.** Surface 2 → Surface Properties → Aperture → Circular Aperture, Min Radius 0, **Max Radius 7.361**.
   Make surface 2 the stop (Surface Properties → Type → "Make Surface Stop"). With Float By Stop Size the entrance pupil follows the
   aperture radius.
3. **Semi-diameters.** For surfaces 5–14 type the value from the table and set the solve to **Fixed** (Solve type "Fixed" on the
   semi-diameter cell), **not Automatic**. This makes the clear apertures (90 % of the diameter) clip rays the way the real lens
   mounts do. Then on surfaces 5–14 also add Surface Properties → Aperture → Circular Aperture, Max Radius = the same value,
   so that rays outside are actually stopped **(verify: in OpticStudio a fixed semi-diameter alone only draws; the aperture
   clips)**.
4. **Materials.** Type the glass names; if OpticStudio reports an unknown glass, check that the SCHOTT catalogue is loaded.
5. **Lens orientation.**
   * LB1199 is symmetric, so orientation does not matter.
   * AC508-150-B and AC254-075-B are used in the catalogue orientation (the crown, strongly curved face toward the eye).
   * **LF1988 is reversed.** Catalogue R1/R2 = +250.0 / +126.3. Reversed, the R 126.3 face meets the light first and both radii change
     sign: −126.3, then −250.0. If you paste the vendor file instead, select its two surfaces and use
     **Lens Data → Reverse Elements (verify)**.

### 2.3 Notes on the table
* The crown/flint thickness splits of the doublets (AC508-150-B 10.0 / 3.2 mm, AC254-075-B 4.5 / 2.1 mm) are my assumptions;
  the vendor `.zmx` files are authoritative (step 2.5).
* AC508-150-B models about 1 % long in EFL with these radii (151 mm at 587 nm), which is within catalogue tolerance.
* The filter is a 3 mm N-BK7 proxy; replace it with the real filter thickness and substrate when it is chosen.
* LB1199 and AC508-150-B nearly touch: 0.5 mm at the vertices, about 4.1 mm at the rim (convex faces facing each other).

### 2.4 First look
1. **Cross-section** (Analyze → Cross-Section, plane XZ). The beam enters at x ≈ −7.7 mm, crosses the two 2-inch lenses
   below the axis, passes the LF1988 near the axis, crosses the axis in the long gap and lands on the **+x** side of the sensor
   (x ≈ 1.0 to 7.4 mm). Compare with `results/design4A_layout.png`.
2. **Footprint diagram** (Analyze → Rays & Spots → Footprint Diagram) on surfaces 10 and 12, all fields. Expected clipping,
   all small:
   * surface 10 (LF1988 front): fields at X = −1.861 mm lose about 4–5 %;
   * surface 12 (AC254-075-B front): fields at X = −13.461, Y = ±7.6 mm lose about 4 %;
   * no clipping on the 2-inch lenses or the stop edge itself.
   Worst-field transmission about **0.95**.
3. **Spot diagram** (Analyze → Rays & Spots → Standard Spot Diagram): Reference = **Centroid**, Show Airy disk on,
   Pattern Square, Rays 20 or more, all wavelengths, all fields.

### 2.5 Compare with the vendor files
For each of the four parts, open the vendor `.zmx` in a separate window, copy its lens rows (Ctrl+C on the rows) and compare
radii, centre thicknesses and glass names with the table in 2.1. Wherever they differ (most likely the doublet thickness splits),
**use the vendor values**. Alternatively, insert the vendor lens directly with **File → Insert Lens (verify)** at the right
surface and delete the hand-typed rows. Keep the air spaces (thicknesses of OBJ and surfaces 3, 6, 9, 11, 14): they are
re-optimised in step 3.

---------------------------------------------------------------------------------------------------------------------------------

## 3. Optimisation (air spaces only; radii and glasses stay catalogue)

### 3.1 Merit function
1. Merit Function Editor → **Optimization Wizard**:
   * Image Quality: **Spot**, Type **RMS**, Reference **Centroid**;
   * Pupil integration **Rectangular Array**, 8 × 8 (or Gaussian Quadrature 6 rings × 6 arms);
   * Assume Axial Symmetry **off** (the stop is off-axis, so the system is not symmetric for one channel);
   * Ignore Lateral Color **off**;
   * untick the wizard's thickness boundary rows (you add your own in 3.3).
2. Click OK. The wizard writes one block of `TRAC`-type rows per field and wavelength.

### 3.2 Variables
Put a **V** on the thickness of:

| Surface | Start | Role |
|---|---|---|
| OBJ | 171.759 | eye → stop |
| 3 | 0.796 | filter → LB1199 |
| 6 | 0.500 | LB1199 → AC508-150-B |
| 9 | 23.912 | AC508-150-B → LF1988 |
| 11 | 88.855 | LF1988 → AC254-075-B |
| 14 | 37.216 | AC254-075-B → cover glass (focus) |

Do **not** vary radii, glass, or the decenters.

### 3.3 Constraints (insert above the wizard rows)

| Operand | Arguments | Target | Purpose |
|---|---|---|---|
| `MNCA` | surf 3 → 3 | ≥ 0.3 | stop plate clear of LB1199 |
| `MNCA` | surf 6 → 6 | ≥ 0.5 | LB1199 / AC508 centre gap |
| `MNEA` | surf 6 → 6 | ≥ 0.5 | edge clearance (redundant here, keep it) |
| `MNCA` | surfs 9 → 9, 11 → 11 | ≥ 1.0 | |
| `MNCA` | surf 14 → 14 | ≥ 8.0 | room for the camera mount |
| `TTHI` | surf 0 → 3 | (no target, weight 0) | eye → first lens; use it in the next two rows |
| `OPGT` | (row of TTHI) | 150.0 | eye → first lens ≥ 150 mm |
| `OPLT` | (row of TTHI) | 205.0 | eye → first lens ≤ 205 mm |

(`MNCA`/`MNEA` = minimum centre / edge thickness for air, `TTHI` = sum of thicknesses; check that TTHI with surface 0 includes the
object thickness **(verify)**; if not, add `THIC` of surface 0 explicitly and sum with `SUMM`.)

### 3.4 Image position and magnification
These rows hold the magnification (0.553) and keep the eye image on its own sensor half. They use the real chief ray (Px = Py = 0)
at the image surface, 0.85 µm:

| Operand | Hx | Hy | Field X (mm) | Target (mm) | Weight |
|---|---|---|---|---|---|
| `REAX` (surf IMA) | −0.8708 | 0 | −13.461 | **+7.420** | 1 |
| `REAX` (surf IMA) | −0.4956 | 0 | −7.661 | **+4.240** | 1 |
| `REAX` (surf IMA) | −0.1204 | 0 | −1.861 | **+1.016** | 1 |
| `REAY` (surf IMA) | −0.4956 | +0.4917 | Y = +7.6 | **−4.205** | 1 |

Hx = X / 15.458 and Hy = Y / 15.458 with radial field normalisation. If your version normalises fields differently, open
Analyze → Rays & Spots → Single Ray Trace for field 4, 5 and 6 and read off the chief-ray x at the image instead.
The sign is positive because the image is inverted.

### 3.5 Run
1. **Optimize → Optimize!** (Damped Least Squares), Automatic cycles; expect the merit to drop only a little because the start
   point is already optimised.
2. **Hammer** for 5–10 minutes, then DLS once more.
3. Make sure the result still meets: eye → first lens 150–205 mm, all gaps ≥ the limits above, magnification 0.53–0.59.

---------------------------------------------------------------------------------------------------------------------------------

## 4. Expected result

### 4.1 Layout and first-order numbers
| Quantity | Expected (tracer) |
|---|---|
| OBJ thickness | 171.76 mm (eye → stop) |
| Surfaces 3 / 6 / 9 / 11 / 14 | 0.80 / 0.50 / 23.91 / 88.85 / 37.22 mm |
| Eye → first lens | 175.56 mm |
| Magnification | 0.553 (image x on the sensor 1.02–7.42 mm; 18.1 µm per pixel in the eye) |
| Working f/# | about 7.2 |
| Worst-field transmission | 0.95 |

### 4.2 RMS spot radius (µm, centroid reference, 0.84/0.85/0.86 µm)
| | X −13.461 | X −7.661 | X −1.861 |
|---|---|---|---|
| Y −7.6 | 10.4 | 5.7 | 7.9 |
| Y 0 | 6.1 | 6.0 | 10.4 |
| Y +7.6 | 10.4 | 5.7 | 7.9 |

Mean 7.8 µm, max 10.4 µm (Design 3: 9.2 / 12.6 µm).
**FFT MTF** at 25 lp/mm (Analyze → MTF → FFT MTF, sampling 64 × 64, max frequency 50): worst field about **0.25**, mean about
**0.55** (geometric × diffraction estimate in my tracer; OpticStudio includes diffraction exactly, so compare the mean first).
**Huygens PSF** at field 5 and at the worst corner (Analyze → PSF → Huygens PSF), plus **Encircled Energy** (Analyze →
Encircled Energy → Diffraction **(verify)**): record the fraction inside a 10 µm pixel (I have no tracer value for this, so it is a new
reference number for later comparison).

### 4.3 If the numbers are far off, check in this order
1. CB pair signs: surface 1 = −7.661, surface 4 = +7.661 (pick-up −1).
2. Ray aiming = Real.
3. **LF1988 reversal**: −126.3 then −250.0 (not +250 / +126.3).
4. Semi-diameters Fixed **and** circular apertures on surfaces 5–14 (otherwise no vignetting appears and spots look too good or too
   bad at the corners).
5. Stop max radius 7.361 (Ø14.72), not 7.0 or 6.0 copied from Design 3.
6. Thicknesses in 2.1, especially the 0.500 mm gap at surface 6.

---------------------------------------------------------------------------------------------------------------------------------

## 5. Analyses to run and save

### 5.1 Standard set
* Spot diagrams and FFT MTF at all nine fields (64 × 64; record 25 and 50 lp/mm).
* Footprints on surfaces 5–14 (vignetting).
* Field curvature / distortion (Analyze → Aberrations → Field Curvature and Distortion). Distortion is calibrated out by the gaze
  fit, but record it.
* Relative illumination (Analyze → Image Quality → Relative Illumination **(verify)**).

### 5.2 Swappable stop plates (Multi-Configuration Editor)
The same barrel takes three stop plates; hole centres stay at ±7.661 mm and only the hole size and the camera focus change.

| Config | Stop plate | Surface 2 max radius | Surface 14 thickness | Light vs Design 3 | Expected RMS mean / max | f/# |
|---|---|---|---|---|---|---|
| 1 | Ø14.7 | 7.361 | 37.216 | 2.04× | 7.8 / 10.4 µm | 7.2 |
| 2 | Ø12.6 | 6.300 | 37.222 | 1.53× | 6.5 / 8.7 µm | 8.4 |
| 3 | Ø10.5 | 5.250 | 37.229 | 1.07× | 5.3 / 7.2 µm | 10.1 |

Multi-Configuration Editor (Setup → Editors → Multi-Configuration):
* Insert 3 configurations.
* Row 1: operand **`APMX`** (aperture maximum radius), surface 2 **(verify the operand name)**: 7.361 / 6.300 / 5.250.
* Row 2: operand **`THIC`**, surface 14: 37.216 / 37.222 / 37.229 (or put a V on it per config and let DLS refocus).

### 5.3 Depth of field (eye moves along the camera axis)
Add configurations, or use a second MCE, with `THIC` surface 0 (OBJ) = 171.759 + dz, all other thicknesses fixed (no refocus):

| dz (mm, + = eye farther) | −2 | −1 | −0.5 | 0 | +0.5 | +1 | +2 |
|---|---|---|---|---|---|---|---|
| Expected RMS mean / max, Ø14.7 (µm) | 34 / 43 | 18.5 / 26 | 11.6 / 18 | 7.8 / 10.4 | 9.4 / 17 | 15.9 / 24 | 31 / 39 |
| Design 3 for comparison | 23 / 32 | 13.3 / 22 | 10.3 / 17 | 9.2 / 12.5 | 10.7 / 17 | 13.9 / 22 | 23 / 33 |

With the Ø10.5 plate the ±1 mm values drop to 13.2 / 11.7 µm (mean), equal to or better than Design 3.
Focus bias: the earlier Design-3 advice (bias 0.5 mm toward the far side) came from a simulation artefact (see
`WIDE_STOCK_SEARCH.md` §4); with the corrected signal model it is not needed. If you still want it, lengthen surface 14 by
m² × 0.5 = **0.15 mm**.

### 5.4 IPD sweep (path length changes with interpupillary distance)
IPD 54 → 74 mm changes the eye → stop path by about −5 → +5 mm (M1 → V = IPD/2 − 7.661). Configurations with OBJ = 171.759 ± 5 mm,
refocus with surface 14 (V on THIC 14 per configuration):

| OBJ change | Surface 14 | m | RMS mean / max | Image x range |
|---|---|---|---|---|
| −5 mm | 38.758 | 0.562 | 8.5 / 11.9 µm | 1.04–7.55 mm |
| 0 | 37.216 | 0.553 | 7.8 / 10.4 µm | 1.02–7.42 mm |
| +5 mm | 35.742 | 0.543 | 7.3 / 10.4 µm | 1.00–7.30 mm |

The camera rail therefore needs about ±1.6 mm of travel to cover the IPD range.

---------------------------------------------------------------------------------------------------------------------------------

## 6. Folded model (periscope + V-prism, both eyes)

1. Save as `D4A_folded.zmx`. Change the OBJ thickness to **30.000** (eye apex → M1).
2. Insert, before surface 1, in the eye's frame:
   * **M1**: Coordinate Break (Tilt About Y = 45°), Mirror surface (Material = MIRROR), Coordinate Break (Tilt About Y = 45°),
     or use **Lens Data → Add Fold Mirror (verify)**, which inserts the three rows for you.
   * Thickness after M1 = **23.839 mm** (M1 → V-prism face = IPD/2 − 7.661 at IPD 63 mm; 19.339–29.339 mm for IPD 54–74 mm).
   * **V-prism face**: second fold mirror at 45° that sends the beam back parallel to the lens axis, displaced to x = −7.661 mm.
   * Thickness after the V face = **117.920 mm** to the stop frame (30.000 + 23.839 + 117.920 = 171.759).
3. In the 3D layout (Analyze → 3D Viewer) confirm the beam leaves the V face parallel to the lens axis and enters hole 1 at
   x = −7.661 mm.
4. **Right eye** = configuration 2 in the Multi-Configuration Editor: flip the signs of both fold tilts (`PRAM` on the tilt parameters
   **(verify)**) and of both CB decenters (surface 1: +7.661, surface 4: −7.661). Keep the field list but flip the field X signs
   (`XFIE` rows **(verify)**), or mirror the eye model.
5. **Equivalence check**: the folded spot diagrams must match the unfolded ones (up to mirror parity).
6. **Path audit**: operand `OPTH` (optical path to a surface) for both configurations at the stop; the difference must be
   **< 0.01 mm** at IPD 63.
7. **Web between the holes**: 2 × 7.661 − 14.72 = **0.60 mm** of plate between the two Ø14.72 holes; the V-prism ridge must be sharp
   (≤ 0.3 mm) and aligned to it. If that is too fragile, use a Ø14.3 plate (1.0 mm web, 1.93× light) and set the stop max radius to
   7.150.

---------------------------------------------------------------------------------------------------------------------------------

## 7. Eye model and Purkinje images

Follow `Zemax_build_guide.md` Part A (Navarro eye; cornea R 7.72, k −0.26, t 0.55; aqueous R 6.50, t 3.05; lens front R 10.2,
k −3.1316, t 4.0, pupil 4 mm; lens back R −6.0, k −1.0, t 16.3203; indices at 0.85 µm 1.3718 / 1.3331 / 1.4130 / 1.3331 **(verify
against the paper)**; LED 17° off the camera axis, mirrored for the other eye; rotation centre 13.5 mm behind the apex.

Checkpoints at straight gaze:

| Quantity | Expected |
|---|---|
| P4 depth relative to P1 | about 0.33 mm deeper |
| P1–P4 separation in the eye | 2.03 mm |
| P1–P4 separation on the sensor (m = 0.553) | **about 112 px** (Design 3: 108 px) |
| Slope | about 0.11 mm per degree of eye rotation in the eye, about 6.1 px per degree on the sensor |

**Image simulation** (Analyze → Extended Scene Analysis → Image Simulation **(verify)**): use each glint as a point object at the
object height from the eye model, with the depth offset entered through the OBJ thickness. Use two P1 points at full intensity and two P4
points at **1.2 % of the P1 flux** (flux, not peak: see `WIDE_STOCK_SEARCH.md` §4), PSF from FFT, 10 µm pixels, 0.85 µm.
Compare with `results/sim_frames_design4A_flux.png`. At the same LED power as Design 3, 4A collects about twice the flux and P1
saturates, so lower the LED or the exposure in the simulation and on the bench.

---------------------------------------------------------------------------------------------------------------------------------

## 8. Cross-talk (non-sequential)

Rebuild the folded model in Non-Sequential mode (File → Convert to NSC Group **(verify)**, or build by hand):
* two Source Rectangle objects 11.6 × 15.2 mm (one per eye), cone ±15–20°, 850 nm;
* M1 mirrors and the V-prism faces as MIRROR objects, the V ridge as an absorbing strip 0.3 mm wide;
* the stop plate as an absorbing plate with **two Ø14.72 mm holes at x = ±7.661 mm**;
* lens barrels and spacer tubes absorbing (SM2 tube over LB1199 + AC508-150-B, SM1 tube over LF1988 and AC254-075-B);
* two Detector Rectangles (left half, right half), 960 × 1080 pixels, 10 µm.

Run left-only and then right-only: **flux on the wrong half / total < 1e-4**. Add a baffle in the 88.9 mm gap. LF1988 only comes with the
visible −A coating, so at 850 nm each face reflects roughly 4 %. Trace the ghost path (Analyze → Ghost Focus Generator, in
sequential mode, **(verify)**) and confirm the double-bounce image is defocused and well below the P4 level.

---------------------------------------------------------------------------------------------------------------------------------

## 9. Tolerancing

1. Tolerance Data Editor → Tolerance Wizard: radius ±1 fringe or ±0.5 %, thickness ±0.1 mm, element decenter ±0.1 mm, tilt
   ±0.1° (TETX/TETY), index ±0.001, Abbe ±0.5 %. Air spaces (surfaces 3, 6, 9, 11) ±0.2 mm.
2. Assembly tolerances: stop decenter ±0.05 mm, sensor decenter ±0.1 mm and tilt ±0.2°, mirror tilts ±0.05°.
3. Compensators: **surface 14 thickness** (camera focus) and sensor decenter X/Y.
4. Criterion: RMS Spot Radius (or Merit Function), Monte Carlo 200 trials.
5. Expected (my Monte Carlo, 60 builds with spacings ±0.2 mm, decenters ±0.1 mm, EFL ±1 %, refocus): 90th percentile mean / max
   RMS **7.9 / 12.3 µm** (Design 3: 9.1 / 13.8 µm). Target: 90 % of trials with max RMS ≤ 13 µm.

---------------------------------------------------------------------------------------------------------------------------------

## 10. Acceptance checklist

| Item | Target |
|---|---|
| RMS spot, all fields (Ø14.7 plate) | mean ≤ 8.5 µm, max ≤ 11 µm (tracer: 7.8 / 10.4) |
| FFT MTF at 25 lp/mm | worst field ≥ 0.2, mean ≥ 0.5 |
| Magnification / image extent | 0.553 / x 1.02–7.42 mm on each half |
| Vignetting | worst field ≥ 0.94 transmitted, no clipping at the stop edge |
| Eye → first lens | 175.6 mm (allowed 150–205) |
| Path-length difference between channels | < 0.01 mm |
| P1–P4 separation | 2.03 mm in the eye, about 112 px |
| Depth ±1 mm (Ø10.5 plate) | mean RMS ≤ 13.5 µm |
| Cross-talk | < 1e-4 |
| Monte Carlo (90 %) | max RMS ≤ 13 µm |

When all rows pass, save the final `.zmx`, export the prescription (Reports → Prescription Data) and the mechanical drawing
(Reports → Lens Drawing **(verify)**), and update `results/design4A.json` and `WIDE_STOCK_SEARCH.md` §3 with the OpticStudio spacings.
