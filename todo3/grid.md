# Lab 3 grid

Tuned HSV pipeline for markers and signs in the shared lane. Scores: −3 to +3; positive cost and energy mean cheap/frugal. CSV sources below are in `results/`. The [scenario](https://ci.mines-stetienne.fr/courses/interacting-humans-real-world/scenario.html) gives the shared-lane, local-processing and privacy constraints. Cost and energy scores are estimates, not measured prices or power.

| Criterion | Score | Weight | Reason | Source |
| --- | --- | --- | --- | --- |
| Latency | 2 | 4 | Even medians: markers 2.75 ms, signs 3.89 ms; full robot response is unmeasured. | `detect-all-tuned.csv` |
| Total cost | 3 | 2 | The two detectors run locally on CPU with numpy/OpenCV; no paid inference or GPU is needed for this implementation. | `detect-all-tuned.csv` (marker/sign rows); `requirements.txt`; scenario |
| Energy | 2 | 2 | CPU image processing takes median 2.75/3.89 ms in even, without training; power was not measured, so this is a qualitative score. | `detect-all-tuned.csv`; `step2.py`, `step3.py` |
| Processing mode | 3 | 2 | One frame per call and a three-step history let the robot react during the 12-step replay rather than after a whole mission. | `policy.csv`; `step6.py` |
| Deployment / sovereignty | 3 | 3 | Detection and decisions run offline on the robot. | [Scenario](https://ci.mines-stetienne.fr/courses/interacting-humans-real-world/scenario.html), shared robot; `step2.py`–`step6.py` |
| Robustness | -3 | 5 | Tuned sign accuracy falls from 0.562 in even to 0.0 in mixed. | `detect-all-tuned.csv` |
| Explainability | 3 | 3 | The shadow mask shows the marker joined to a floor shadow. | `confusions-all.csv`, shadow marker failures; `shadow.png` |
| Confidentiality | 1 | 3 | Frames can stay local, but the real camera films identifiable people. | [Scenario](https://ci.mines-stetienne.fr/courses/interacting-humans-real-world/scenario.html), camera in a shared workshop; report §6 |
| Maintainability | 1 | 2 | A few constants are easy to change, but all five conditions need checking. | `detect-all-change.csv`, `detect-all-tuned.csv` |
| Human control | 2 | 5 | The 12 policy steps have 0 forbidden outcomes; unknown causes stop/report. | `policy.csv` |

Robustness and human control have weight 5 because errors affect people in the lane; latency has 4 for a proposed 100 ms cycle; offline operation, explanations and confidentiality have 3; other criteria have 2. Weighted total: 42. [Radar](radar.png).

For EC8, keep this as the baseline and marker reader. I accept poor lighting robustness to get simple local processing, but 0.0 sign accuracy in mixed light rules out using it alone for traffic safety. Add an obstacle sensor and a physical stop.

Next checks: new images under each light condition, a no-target video counted by false-stop events, and measured braking/response time. Proposed targets: sign recall ≥0.95 per condition, <1 false stop/minute and p90 response ≤100 ms. They have not been reached or measured here. Repeated false stops risk operators bypassing the system; uncertainty needs an explanation and supervised recovery. Keep real camera frames in RAM, with restricted diagnostic captures deleted within 24 hours.
