# meta_2026

Produce inspection and stock-priority assistant combining batch history,
sensor evidence, guided investigations and human-confirmed stock actions.
The product name is undecided.

## Project documents

- [Product and build plan](docs/product_build_plan.pdf): unified product flow,
  model roles, scoring, implementation milestones and evaluation.
- [Repository architecture](docs/repository_architecture.md): current runtime,
  complete directory structure, planned files, ownership boundaries and known gaps.
- [Model validation](docs/model_validation.md): live Muse/SAM results, mask preview,
  tested environment and rerun instructions on the model-validation branch.
- [Video model-flow demo](docs/video_model_demo.md): four-model video run, private
  interactive replay link, timeline, real outputs and reproduction instructions.
- [Model report card](docs/model_report_card.md): measured results, unknown accuracy
  metrics and recommendations about retrieval and fine-tuning.
- [Physical testing roadmap](docs/testing_roadmap.md): blind item-level evaluation,
  sensor characterization and controlled mixed-crate removal experiments.
- [Narrated walkthrough and screenshots](docs/media/README.md): checked-in MP4,
  captions, transcript, chapter timestamps and lab captures.
- [Standalone lab](demos/video-model-flow/README.md): checked-in replay videos,
  audio and checkpoint snapshots; runs locally without a key or hosted-site login.

The existing application is a React/Vite dashboard, FastAPI telemetry API,
Python inference worker and ESP32-S3 sensor firmware. Most new product folders are
documented scaffolding. The Meta adapters now provide live-tested perception and
read-only planning boundaries; the complete product workflow is not yet wired in.
Existing runtime entry points and deployment scripts remain in place.
