# Build guide: single-sensor binocular dual-Purkinje tracker with Thorlabs stock lenses

Status: **simulated design, not yet built.** Everything below was produced by the in-repo Python ray tracer
(`src/`), not by OpticStudio. Items marked **(verify)** come from memory or placeholders and must be checked
against vendor data before ordering or machining.

Figures: `results/optical_system_design.png` (layout), `results/spots.png`, `results/sim_frames.png`, `results/sim_analysis.png`.

---------------------------------------------------------------------------------------------------

## 0. What you are building

One Lux19HS camera (1920×1080, 10 µm px, mono, global shutter, 2247 fps max) watches **both eyes at once**.
Each eye is relayed by a 45° mirror (M1) to a central V-prism whose knife edge splits the two beams; both beams
pass a dual-hole stop and **one shared objective**, and land on the left and right halves of the sensor.
The measurement is the **P1−P4 vector** (first and fourth Purkinje images) of each eye, 850 nm illumination, head fixed.

| Item | Value |
|---|---|
| Magnification | 0.55 (18.2 µm per pixel in the eye) |
| Eye field per eye | 11.6 × 15.2 mm |
| IPD (nominal / range) | 63 mm / 54–74 mm |
| Wavelength | 850 nm (±5 nm band-pass) |
| Sensor split | two 9.6 × 10.8 mm halves, 0.72 mm dead gap at the centre |

## 1. Bill of materials

| Qty | Part | Notes |
|---|---|---|
| 1 | Lux19HS camera, CXP-12 ×4, frame grabber | exposure ≤ 445 µs at 2247 fps |
| 1 | Thorlabs **AC254-150-B** (f 150, Ø25.4, N-BK7/SF5, 650–1050 nm AR) | mounted **reversed** (see §3) |
| 1 | Thorlabs **AC254-075-B** (f 75, Ø25.4, N-BAF10/N-SF6HT, 650–1050 nm AR) | standard orientation |
| 1 | 850 nm band-pass filter Ø25 mm (e.g. FBH850-10) | at the stop (**verify** thickness/substrate; model uses 3 mm) |
| 2 | 25 mm IR-coated flat mirrors, 45° mounts (M1) | |
| 1 | V-prism / two 45° mirrors with knife edge (ridge ≤ 0.3 mm) | |
| 1 | Black anodized stop plate, two Ø6.25 mm holes, 13.0 mm apart | |
| 1 | SM1 lens tube + 2 retaining rings + ≈3.0 mm spacer ring | |
| 1 | Septum plate (absorbing) from lens rear to sensor | cross-talk control |
| 2 | 850 nm LEDs, ~17° off axis, ≥300 mm away (or 1 per eye, mirrored) | check IEC 62471 before use |
| 1 | Model eye (see §6) + rotation stage (±15°, pivot 13.5 mm behind cornea) | |
| 1 | USAF-1951 / dot-grid target, backlit at 850 nm | focus and magnification |

## 2. Final optical prescription (stock lenses)

Unfolded, one channel (the other is the mirror image). z = 0 at the stop; distances in mm.

| Element | Surface radii (mm) | Glass | Thickness (mm) | Gap after (mm) |
|---|---|---|---|---|
| Stop (Ø6.25, at x = ∓6.5) + filter front | flat | filter, 3.0 thick | 3.0 | 0.50 (air) |
| AC254-150-B, **reversed** (catalogue R1/R2/R3 = 91.6 / −66.7 / −197.7) | +197.7, +66.7, −91.6 (eye side first) | SF5 2.5, then N-BK7 5.4 **(verify split)** | 7.9 | **0.30** |
| AC254-075-B (catalogue R1/R2/R3 = 36.90 / −42.17 / 417.8) | +36.90, −42.17, +417.8 | N-BAF10 4.5, then N-SF6HT 2.1 **(verify split)** | 6.6 | **71.13** (to cover glass) |
| Sensor cover glass | flat | 1.0 mm (verify) | | 0.5 to die |

Key distances: **eye → stop 134.84 mm** (eye → first lens ≈ 138 mm), filter → lens A 0.50, lens A → lens B 0.30
(vertex to vertex), lens B → cover glass 71.13. The two lenses are essentially in contact; because both vertices bulge
into the gap, the spacer ring length at the lens edges is ≈ gap + edge sags ≈ **3.0 mm (verify against the lens STEP files)**.

Why this pair: 272 single and two-lens stock combinations from your Thorlabs list were optimised for m = 0.55; this
pair gave the lowest merit (`results/stock_search_*.json`, `results/stock_refined.json`, `src/stock_final.py`).
At the originally wanted 149.4 mm the same pair only reaches m ≈ 0.49–0.50.

### Predicted performance (design wavelength 840–860 nm)

| Check | Result |
|---|---|
| RMS spot, 9 fields (µm) | 6.3 – 16.6 (centre 9.5; corners 12–17) |
| Magnification | 0.550 |
| Image extent on sensor half | x 0.36–6.79 mm (half is 0–9.6 mm) |
| Vignetting | none (clear apertures 90% of Ø25.4) |
| MTF at 25 lp/mm (geometric × diffraction, f/14) | min 0.12, mean 0.28 (diffraction limit 0.62) |

This is **not** diffraction-limited-quality: expect 1–2 px blur of each glint. That is acceptable for centroiding but
below the 0.40 MTF goal set for the custom surrogate design. A custom objective would fix this.

## 3. Mechanical layout (folded, IPD 63 mm)

```
eye ──30──▶ M1 ──25.0──▶ V-prism ──79.84──▶ stop+filter ─▶ lens A ─▶ lens B ─71.13─▶ cover ─▶ sensor
```
* eye apex → M1: 30 mm. M1 → V-prism face: IPD/2 − 6.5 = 25.0 mm (20.5–30.5 mm over IPD 54–74 mm).
* V-prism → stop: 134.84 − 30 − 25 = 79.84 mm. Both channel path lengths must match to < 0.05 mm.
* The beams leave the V at x = ±6.5 mm and run **parallel to the optical axis** through the holes (±6.5 mm).
* IPD change moves M1 only; refocus the camera along the rail by ≈ m²·Δz (±1.5 mm for ±5 mm path change).

## 4. Step-by-step build

1. **Safety first.** Choose LED power from IEC 62471 / ANSI Z136.1 limits (a few mW at the cornea at most); measure before any human use. Bench work uses the model eye only.
2. **Reproduce the design in OpticStudio.** Download the `.zmx` files for AC254-150-B and AC254-075-B from the Thorlabs product pages. Follow `Zemax_build_guide.md` Part B, replacing its surface table with §2. Check your numbers against §2 (spot sizes, m = 0.55, image at x = +3.5 mm). Any difference larger than ≈5% means a transcription error here; tell the repo owner.
3. **Pre-assemble the objective.** In an SM1 tube: stop+filter (stop plate pressed against the filter front face), 0.50 mm air (shim), lens A **flint (SF5) side toward the eye** i.e. reversed from Thorlabs' standard orientation; the engraved crown/N-BK7 face toward the camera. Then the ≈3.0 mm spacer, then lens B with its R1 = 36.9 mm face toward the eye. Retain with rings; do not over-tighten (stress birefringence).
4. **Mount the camera** on a linear rail (≥ 10 mm travel, ≤ 5 µm resolution) so lens-B-to-cover distance can be tuned around 71.1 mm. Mount the septum from the lens rear to the sensor plane on the centre line.
5. **Place the stop plate**: holes at x = ±6.5 mm about the lens axis; the lens axis must pass through the V knife edge.
6. **Align the periscope**: M1 mirrors at 45° (autocollimator), V-prism ridge on the lens axis (laser along the axis should split equally between left and right channels), path lengths equal.
7. **Focus and magnification**: place the backlit target at the eye plane of each channel (134.84 mm from the stop, unfolded). Move the camera until the 9-point grid is sharp; target pitch gives m (expect 0.55 ± 1%).
8. **Locate the images**: confirm each eye image sits in its own half with the inner edge ≥ 0.3 mm from x = 0. If one image crosses the centre, shift the V-prism or the camera laterally.
9. **Install the model eye** on the rotation stage, pivot at the eye's centre of rotation (13.5 mm behind the cornea apex), cornea on the optical axis of channel 1; repeat for channel 2 (or mirror-image a second eye).
10. **Illumination**: mount the LED 17° off axis at ≥ 300 mm; check P1 and P4 are both visible with exposure ≤ 445 µs (§5 gives the expected signal levels).
11. **Calibration**: record a 5×5 grid, ±12°, 20 frames each; run `src/simulate_images.py` analysis functions (`detect`, `feature`, `design_matrix`) on the real frames and fit the 2nd-order map (§5).
12. **Validation**: independent 7×7 grid ±15°; compare error to §5. Then test depth sensitivity (move the eye ±1 mm along the camera axis) and IPD changes.
13. **Tolerance and cross-talk checks**: run the OpticStudio tolerancing/cross-talk parts (Zemax guide Parts D–E) with the real `.zmx` files.

## 5. Model eye: simulation and image analysis (done here)

**Eye model.** Navarro (1999) relaxed eye (`src/eye.py`): cornea R 7.72 mm (conic −0.26), aqueous 3.05 mm, lens 4.0 mm, centre of rotation 13.5 mm behind the apex, 850 nm indices. P1 is the virtual image behind the cornea (≈ 3.9 mm); P4 is the inverted real image of the back lens surface ≈ 0.3 mm deeper. Source 17° off the camera axis (mirrored for the second eye).

**Image formation.** For each gaze direction the P1 and P4 positions are propagated through the stock objective by ray tracing (60-ray pupil grid, 850 nm), blurred with a 5 µm Gaussian (Airy-core stand-in), binned into 10 µm pixels, noise added (shot, 8 e⁻ read, 10-bit, 15 ke⁻ assumed full well). P1 peak ≈ 9 ke⁻ (618 DN), P4 = 1.2% of P1 (**verify, depends on LED and cornea reflectivity**). Result frames: `results/sim_frames.png`.

**Analysis pipeline** (`detect`, `feature`):
1. Median-filter background subtraction per half-frame.
2. P1 = brightest peak; P4 = next peak outside a 25 px mask (accepted if > 6σ).
3. Local centroid (threshold at 15% of the peak, 11×11 px window).
4. Feature = (P1−P4 vector in px) × 10 µm / m, in mm of eye space.
5. Gaze map: 2nd-order polynomial (6 terms per axis) fitted on a 5×5 calibration grid (±12°).

**Results (left eye, noisy frames; `results/sim_summary.json`):**

| Quantity | Value |
|---|---|
| P1−P4 separation, straight gaze | 112 px (≈ 2.0 mm in the eye) |
| Feature gain | ≈ 9.4° per mm of P1−P4 in the eye (≈ 0.105 mm/°), i.e. ≈ 5.8 px per degree on the sensor |
| Gaze error, 7×7 test grid ±15° | RMS 0.11°, max 0.33° |
| Gaze error inside ±12° | RMS 0.05° |
| Precision (200 noisy frames, one pose) | 0.009° (yaw) / 0.019° (pitch) |
| P1−P4 centroid noise | 0.13 px (x), 0.06 px (y) |
| Eye depth shift ±1 mm / ±2 mm | RMS error 0.15° / 0.25–0.30° (the one sensitive axis; hold the head to ≲ ±0.5 mm) |
| Lateral eye shift ±0.5 mm | no measurable change (0.05–0.07°): common to P1 and P4 |

(The errors outside ±12° come from the polynomial fit extrapolating beyond the calibration grid; calibrate on ±15° to reduce.)

## 6. Physical model eye options (verify before buying)
* A purpose-made artificial eye (cornea radius ≈ 7.8 mm, anterior chamber, lens, retina) gives P1 and P4; a single polished ball lens gives P1 only.
* Mount it on a rotation stage whose axis passes ≈ 13.5 mm behind the cornea apex; use an encoder as the gaze truth.

## 7. Known gaps and risks
1. **Lens data**: radii and glasses are transcribed from `Thorlabs_Stock_Lens_Reference.md` and agree with catalogue EFL within 1%, but glass dispersion data (N-BAF10, N-SF10, N-SF6HT≈N-SF6, SF5) were typed from memory and the crown/flint thickness split of each doublet is **assumed**. Replace with the vendor `.zmx` files.
2. **MTF**: the stock pair does not meet the 0.40 @ 25 lp/mm target; corner glint blur is 12–17 µm RMS (1–2 px).
3. **Filter and cover glass** thicknesses and substrates are placeholders.
4. **Not done**: non-sequential cross-talk model, Monte Carlo tolerancing, IR safety calculation, a physical-eye validation, and the folded-layout ray trace (only analytic path lengths; layout figure is schematic).
5. **P4/P1 intensity ratio** and sensor full-well/gain are assumptions; measure with the real camera.
6. Sensor frame mapping assumes the periscope preserves lateral parity; confirm with the target image (flip the image in software if not).
