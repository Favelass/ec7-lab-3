# Lab 3 report

Frédéric Dardinier

The results use the 250 supplied images. Baseline settings: blue saturation >100, fill 0.68–0.93, circularity ≥0.72. The final code uses the stricter settings from step 5 (`-tuned` results).

## 1. Markers

From `results/detect-all.csv`:

| condition | accuracy | distance_mae_m |
| --- | --- | --- |
| even | 0.971 | 0.037 |
| low-sun | 0.893 | 0.021 |
| shadow | 0.811 | 0.016 |
| mixed | 0.848 | 0.013 |

`CLOSE_HEIGHT_PX = 81`. Sheets 3 and 4 are both read in `even`: 2/2 and 8/8 respectively. Their patterns are `krgk` and `kgrk`. If no box or pattern matches, the result is `unknown`.

Success: [mask](success.png), [input](success-input.jpg), from `even-040`. Sheet-3 is read at 1.161 m; the labelled distance is 1.192 m.

## 2. Signs

From `results/detect-all.csv`:

| condition | family_accuracy | accuracy | distance_mae_m |
| --- | --- | --- | --- |
| even | 0.75 | 0.625 | 0.074 |
| low-sun | 0.591 | 0.591 | 0.075 |
| shadow | 0.846 | 0.846 | 0.058 |
| mixed | 0.0 | 0.0 | n/a |

The shape tests use fill and circularity (`4πA/P²`). The largest white component inside the blue disc gives the arrow direction: its long axis gives vertical/horizontal, and its wider end gives the head. Reading the unclosed colour mask preserves small arrows.

In `even`, two up arrows are still read as right; three left arrows and one down arrow are missed. See `results/confusions-all.csv`.

## 3. Distance

`distance = 530 × real_seen_size / apparent_size`, with sizes from `assets/geometry.json`. Bearing is `atan(horizontal_offset / 530)` in degrees.

| target | outer size (m) | mask ratio | size used (m) | distance_mae_m in even |
| --- | --- | --- | --- | --- |
| marker | 0.2015 | 1 | 0.2015 | 0.037 |
| stop sign | 0.07 | 57/70 | 0.057 | n/a |
| direction sign | 0.07 | 67.9/70 | 0.0679 | 0.074 |

The marker size is the 201.5 mm printed band, not the 210 mm paper height. The two sign-mask ratios are 57/70 ≈ 0.8143 and 67.9/70 = 0.97, both below 1. The white free-sign disc uses the full 0.07 m diameter.

Using the full disc size for the red mask would overestimate distance by about 23%; for blue, about 3%. There are no stop signs in `even`, so its stop-distance MAE is unavailable. The engine measures distance error only on correctly named targets.

## 4. Lighting and the blue threshold

Change: blue saturation >100 to >60. Comparison of `detect-all.csv` and `detect-all-change.csv`:

| condition | detector | accuracy before | accuracy after |
| --- | --- | --- | --- |
| even | marker | 0.971 | 0.971 |
| even | sign | 0.625 | 0.688 |
| low-sun | marker | 0.893 | 0.893 |
| low-sun | sign | 0.591 | 0.636 |
| shadow | marker | 0.811 | 0.811 |
| shadow | sign | 0.846 | 0.846 |
| mixed | marker | 0.848 | 0.848 |
| mixed | sign | 0.0 | 0.529 |

There are no targets in `absent`, so accuracy is undefined there. The before/after false-positive rates are:

| condition | detector | FP rate before | FP rate after |
| --- | --- | --- | --- |
| absent | marker | 0.08 | 0.08 |
| absent | sign | 0.08 | 0.08 |

Shadow failure: [mask](shadow.png), [input](shadow-input.jpg), from `shadow-007`. The extra dark strip crosses the white bands and continues onto the floor. It joins the marker mask to the floor, so the box is rejected as `unknown` before band reading. No sheet-6→sheet-7 confusion occurs in this run; four of nine shadowed sheet-6 images are rejected.

Under mixed light, washed-out pixels lose saturation: sign accuracy is 0.0, versus 0.848 for markers. Lowering the blue threshold raises sign accuracy to 0.529, with the absent false-positive rates unchanged at 0.08. It helps on this set, but still misses 8/17 signs. The threshold was restored to >100 as requested.

## 5. False positives

Final shape settings: `FILL_MIN=0.72`, `FILL_MAX=0.88`, `CIRCULARITY_MIN=0.80`.

Baseline: [detect-absent.csv](../results/detect-absent.csv) and [confusions-absent.csv](../results/confusions-absent.csv). Final run: [detect-absent-tuned.csv](../results/detect-absent-tuned.csv) and [detect-all-tuned.csv](../results/detect-all-tuned.csv).

| detector | FP/min before | FP/min tuned |
| --- | --- | --- |
| marker | 48.0 | 48.0 |
| sign | 48.0 | 0.0 |

Before tuning, four absent images are read as sheet-9 and four as stop signs. Afterwards, only the four sheet-9 errors remain (`confusions-absent-tuned.csv`). At the engine's 10 fps, 4/50 gives 48 false-positive frames/minute, not 48 separate braking events.

Cost on the other conditions (`detect-all.csv` versus `detect-all-tuned.csv`):

| condition | marker before | marker tuned | sign before | sign tuned |
| --- | --- | --- | --- | --- |
| even | 0.971 | 0.971 | 0.625 | 0.562 |
| low-sun | 0.893 | 0.893 | 0.591 | 0.591 |
| shadow | 0.811 | 0.811 | 0.846 | 0.692 |
| mixed | 0.848 | 0.848 | 0.0 | 0.0 |

The stricter filter removes absent stop detections but misses more real signs, especially in shadow. False detections on the other family also remain: tuned sign FP rates are 0.088 in even, 0.286 in low-sun and 0.081 in shadow.

False positive: [mask](false-positive.png), [input](false-positive-input.jpg), from `absent-001`. A dark prop is read as sheet-9, including after tuning. The three masks were copied from `out/`.

## 6. Policy

`results/policy.csv`: 0 forbidden outcomes in 12 steps.

- A person ahead always causes a stop.
- A stop sign causes slowing, then stopping from 0.7 m, leaving a margin before 0.3 m. At 1.2 m the replay slows; at 0.6 and 0.3 m it stops.
- A close stop sign below confidence 0.5 still causes a stop. Other signs below 0.4 cause `report` (stop and explain).
- A lost stop sign stays in the recent history. `unknown` causes stop if that stop has not been made, otherwise `report`.
- Left/right turn, down stops, up/free allow forward motion after the confidence check.

Proposed confidence thresholds: 0.3 for a person and 0.5 for a stop sign. Using 0.5 for both could reject a person detection at confidence 0.4 even though missing that person risks a collision; the lower person threshold accepts that case, at the cost of more false stops. This is not calibrated: the engine supplies only `person_ahead`, not a person detector. Braking and motor response were not measured.

For real camera use: process frames in RAM and discard after inference; restrict exceptional diagnostic captures to authorised operators and delete them within 24 hours.
