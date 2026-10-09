# Does 2-inch optics buy more light? (stop-diameter study, eye -> first lens 205 mm)

Light collected scales with the stop area (D^2), not the lens diameter. Two identical doublets, standard orientation, re-optimised
(ts, gap, eye distance, sensor distance) for each stop diameter D; hole offset = max(6.5, D/2 + 0.3) mm; 840-860 nm; `src/study_2inch.py`,
raw data `results/study_2inch.json`. Same caveats as the other stock-lens documents (glass data, thickness split).

| Lenses | D (mm) | f/# | Light vs D=6.25 (after vignetting) | RMS spot, min-max (mean) um | Vignetting | MTF25 min/mean |
|---|---|---|---|---|---|---|
| AC254-150 x2 (1 in) | 6.25 | 22.4 | 1.0x | 3.6-8.3 (6.5) | none | 0.18/0.32 |
| | 9 | 15.6 | 2.1x | 6.4-12.4 (10.1) | none | 0.08/0.34 |
| | 12 | 11.6 | 3.4x | 9.1-16.9 (13.4) | 8% | 0.02/0.29 |
| | 15 | 9.3 | 4.1x | 10.2-21.5 (15.7) | 29% | 0.06/0.25 |
| | 18 | 7.7 | 4.6x | 11.6-27.2 (18.2) | 44% | 0.03/0.23 |
| AC508-150-B x2 (2 in) | 6.25 | 22.4 | 1.0x | 5.8-10.8 (8.5) | none | 0.07/0.27 |
| | 9 | 15.6 | 2.1x | 9.7-16.4 (13.3) | none | 0.03/0.27 |
| | 12 | 11.6 | 3.7x | 15.8-24.2 (20.3) | none | 0.01/0.18 |
| | 15 | 9.2 | 5.8x | 30.3-40.9 (35.6) | none | 0.04/0.12 |
| | 18 | 7.7 | 8.3x | 51.7-63.6 (57.1) | none | 0.03/0.09 |

Findings
* 2-inch optics remove vignetting but not aberrations: spot size grows roughly linearly with D for both pairs, and the AC508-150-B pair is
  worse than the 1-inch AC254-150 pair at every D (different glass/radii, asymmetric for this finite conjugate).
* Best practical step with stock parts: **1-inch AC254-150 x2 with D = 9 mm gives 2.1x light** for a mean spot of 10 um (about 1 px); beyond that
  (D >= 12 mm) vignetting and aberrations dominate.
* The biggest single light gain is a shorter eye distance: the 138 mm stock design (AC254-150 reversed + AC254-075-B) works at f/14 with the 6.25 mm
  stop, i.e. ~2.3x more light than the 205 mm design at the same stop, with similar spot size.
* Larger D also costs depth of field (blur grows with D) and needs a wider hole spacing from D >= 12 mm (hole offset above 6.5 mm).

## Adding a third stock element (stop diameter 12 mm, eye -> first lens 195-205 mm)
`src/search3.py` (168 configurations: the two best pairs plus one extra stock lens - plano-convex, biconvex, meniscus, best-form or negative - in front, in the
middle or behind), then `src/refine3.py` with wider spacing limits. Data: `results/search3_D12.json`, `results/search3_refined_D12.json`.
The search is a beam extension, not exhaustive, and uses one optimiser start per configuration.

| Design (all N-BK7 singlets/AC doublets, standard orientation unless noted) | RMS mean / max (um) | MTF25 min / mean | f/# | Vignetting | m | Eye -> lens |
|---|---|---|---|---|---|---|
| 2 x AC254-150 (reference, from the table above) | 13.4 / 16.9 | 0.02 / 0.29 | 11.6 | 8% | 0.59 | 205 |
| LBF254-200 (reversed) + AC508-150-B + AC254-150 | **9.2 / 12.6** | 0.08 / **0.44** | 10.3 | 8% | 0.53 | 199 |
| AC254-150 + AC254-150 + LBF254-200 | 10.9 / 15.7 | 0.13 / 0.40 | 10.5 | 7% | 0.53 | 205 |
| AC508-150-B + AC254-150 + LA1229 | 12.8 / 16.3 | 0.01 / 0.33 | 10.6 | 1% | 0.53 | 205 |

* A third stock element recovers part of the aberration cost of the larger stop: mean spot 13.4 -> 9.2 um and mean MTF25 0.29 -> 0.44 at the same f/10-11,
  i.e. about 4.5x the light of the f/22 design with spots around one pixel.
* The best designs put the extra best-form lens (f 200) far from the others with a long gap (60-110 mm) and the last lens only 30-45 mm in front of the sensor; the
  tube is therefore long (roughly 250-300 mm from filter to sensor) and the lenses are not bunched together.
* Worst-field MTF25 stays low (0.01-0.13) and vignetting is still 1-8%; these are not yet clean designs. Magnification drifted to 0.53 (outside the earlier 0.55 target).
* The spacings were found by Nelder-Mead from one start and are likely local optima; a proper multi-start or global search could improve them.
