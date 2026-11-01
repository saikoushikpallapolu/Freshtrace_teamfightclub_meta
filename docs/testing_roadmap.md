# Mixed-crate testing roadmap

The proposed demonstration is: photograph mixed produce, flag visible concerns,
confirm/remove the affected items, and compare the crate-level sensor response.
That is useful only if camera identification, instrument behavior and the physical
intervention are tested separately before being combined.

## Product claim for the pilot

"The app highlights tomatoes with visible deterioration, recommends inspection,
and records whether the crate-level sensor response changes after removal."

A single crate-level sensor does not chemically identify individual tomatoes.
Use "visually normal" and "visibly deteriorated" reference labels; these are not
microbiological food-safety labels. Keep mixed experimental produce out of sale
or consumption. No real trial results are claimed by this roadmap.

## 1. Add item-level visual evidence

Crate photo -> SAM masks -> Spark appearance observations linked to each mask ->
inspect/no visible concern/unclear flags -> human confirmation.

Start with a shallow, single-layer tray. Record image-local object ID, source
photo/mask/crop, observation, inspection category, independent reference label and
outcome. Hidden surfaces require another view. IDs must not be assumed stable
after rearrangement; save the new photo and confirm correspondence where needed.

## 2. Characterize the sensor procedure

Fix container, lid/airflow arrangement, sensor placement, quantity/mass, timing and
handling. Record temperature/humidity, raw VOC/NOx, processed indices, actual
timestamps and device/session identity. Mark baseline, exposure, opening/handling
and recovery phases within the continuous stream.

Follow manufacturer conditioning/run-in requirements. Choose validity windows from
pilot measurements, not arbitrary short waits. Raw VOC and processed Index have
different meanings/directions; not every numeric channel should decrease after
removal. The processed algorithm adapts to its environment.

Review existing firmware timing: network reconnect/processing must not silently
disrupt the algorithm's configured sampling interval. A five-reading software
baseline is not proof of physical stabilization. Existing risk weights and the
percentage floor are unvalidated heuristics.

References: [SGP41 datasheet](https://sensirion.com/resource/datasheet/sgp41),
[Sensirion Gas Index Algorithm](https://github.com/Sensirion/gas-index-algorithm).

## 3. Sensor feasibility gate

Measure an empty container, visually normal produce, visibly deteriorated produce
and mixed produce under comparable conditions. Randomize order where practical;
recover to the declared baseline condition between comparable measurements.

An initial engineering screen can use 10 matched comparisons. Declare direction,
validity and separation rules first. Report independent sample sets separately
from repeated readings. If responses overlap heavily, investigate setup before AI.

## 4. Blind camera evaluation

A teammate assigns reference labels before seeing predictions, using a fixed
visual checklist. Keep labels and affected-item count out of the model input.
Include all-normal, mixed, ambiguous, different positions, shadows, harmless marks
and partially hidden deterioration. Use separate physical batches for development
and held-out evaluation. Count misses, false alarms and unresolved cases.

## 5. Controlled removal experiment

| Arm | Intervention | Confound addressed |
| --- | --- | --- |
| A: targeted | Remove app-flagged, human-confirmed affected tomatoes | Intended intervention |
| B: normal removal | Remove a comparable number/mass of visually normal tomatoes | Reduced produce quantity |
| C: sham | Open/handle for the same duration; remove nothing | Ventilation and handling |

Use comparable mixed arrangements and random assignment. For each run:

1. Record a valid pre-intervention window.
2. Save the app prediction before revealing reference labels.
3. Timestamp and perform the assigned intervention.
4. Exclude the handling transient from the comparison.
5. Apply the same settling/recovery validity rule.
6. Record the post-intervention window.
7. Compare changes across arms, including inconsistent/unresolved runs.

A lower graph alone is not success. Look for a reproducible targeted-removal effect
beyond control-arm changes. Aim for several independent arrangements per arm;
small counts support a feasibility claim only. Do not force immediate recovery or
declare remaining stock fresh when the sensor improves.

## 6. Full workflow and disagreements

Register -> capture -> item flags -> valid session -> human inspection/removal ->
remeasure -> recorded outcome and due check.

- Visual concern with low sensor response: retain the inspection flag.
- Sensor deviation without a visible culprit: request inspection or a validated group test.
- Occlusion: request another view.
- Instability/disconnection: sensor evidence unavailable, not reassuring zero.
- No recovery: stop unresolved.

Wonder proposes allowed next steps; code enforces validity, device reservation and
stopping rules. Start with the [model report-card metrics](model_report_card.md).
Add retrieval/tuning only in response to measured errors, after this baseline.
