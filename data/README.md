# Data and evidence

Existing tomato CSV files and session fixtures stay at their current paths.
Their scientific provenance has not been established by the architecture review.
`scripts/stitch_datasets.py` constructs a synthetic timeline; synthetic time is not
real longitudinal evidence. Keep replay/simulation labels in all evaluation exports.

- `fixtures/`: existing valid/bad telemetry and synthetic replay inputs.
- `raw/`: ignored runtime JSONL produced by ingestion.
- `processed/`: ignored derived measurements.
- `media/`: ignored private photo/mask files, except its directory README.
- `evaluation/`: sanitized manifests/results approved for source control;
  generated `runs/` stays ignored.

Real observations should retain batch/session IDs, actual capture times, protocol
version and raw evidence references. Do not commit private uploads or credentials.
