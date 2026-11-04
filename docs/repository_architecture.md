# Repository architecture

For installation and dashboard URLs, use [setup.md](setup.md). This document maps the current source and runtime boundaries; the [implementation plan](phased_implementation_plan.md) tracks future work.

## Runtime entry points

| Process | Command | Port | Responsibility |
| --- | --- | --- | --- |
| Visual API | `python scripts/run_product.py` | 8080 | Batches, photos, perception jobs, saved evidence and reviews |
| Sensor API | `python scripts/run_product.py --mode sensor` | 8081 | Device status/history, ingestion and notifications |
| Frontend | `npm --prefix frontend run dev` | 5173 | Visual workspace at `/`; sensor dashboard at `/?view=device` |
| AWS worker | `python scripts/run_product.py --mode worker` | None | Consume SQS telemetry, infer sensor state, persist evidence and alert |
| Model lab | `python scripts/smoke/preview_video_site.py --directory demos/video-model-flow` | 8767 | Local replay of recorded four-model results |

The launcher loads root `.env` without overriding shell values, sets the working directory, and binds development APIs to loopback. Vite reads public configuration from root `.env` and routes the two APIs to their default ports. Direct API-factory use reads explicit process environment; it does not load cloud credentials implicitly.

## Visual inspection

`frontend/src/pages/BatchWorkspace.jsx` handles batch registration, capture, history, and observation selection. `InspectionPanel.jsx` displays item findings, exact-mask hit testing, category filters, provider receipts, and separate human reviews. `SamplePicker.jsx` imports attributed, checksummed public images.

`src/backend/api/product.py` configures the standalone FastAPI application. Its lifespan applies migrations and starts a single perception worker when a Meta key/provider is configured. Endpoints are divided into `batches.py`, `inspection.py`, and `samples.py`.

The perception workflow records an observation and a durable queued job. A compare-and-update claim prevents two workers from processing one queued attempt. An attempt runs at most two provider calls:

1. SAM 3.1 locates tomato regions on the normalized analysis image.
2. Spark receives scene context and labeled crops, and returns structured visual observations and visibility limits.

The pipeline verifies the returned object IDs against the segmentation, writes masks/crops/overlays/hit maps, and persists model-call receipts. Results are retrieved from storage; selecting an item or viewing a saved result does not run inference. Failed/expired work is marked durably and requires an explicit retry. Human reviews append records rather than replace model findings.

`src/backend/meta/planner.py` provides a bounded, read-only Wonder tool loop over supplied batch history. Voice transcription and the four-model video flow are exercised through explicit validation scripts and recorded lab artifacts; they are not photo-workspace buttons.

## Storage and database

| Source | Purpose |
| --- | --- |
| `persistence/product_models.py` | Batch, media, observation, job, review, model-call and request-receipt tables |
| `persistence/models.py` | Sensor sessions, raw telemetry, event records and full state snapshots |
| `persistence/repositories.py` | Batch-scoped lookups, transactional writes and durable retry receipts |
| `persistence/runtime.py` | SQLite/PostgreSQL engine configuration and schema initialization |
| `persistence/migrations/` | Ordered Alembic upgrades |
| `storage/media.py` | Bounded JPEG/PNG validation, normalized pixels and immutable originals |

The visual API defaults to `product_local.db` and `data/media/uploads`. The sensor service defaults to `backend_local.db`, or an explicitly configured PostgreSQL/RDS URL. The API and SQS worker share the sensor database. New snapshots retain the complete computed result so risk components and velocity remain available across processes. Older rows retain only fields originally recorded; missing components remain unavailable.

Migrations are additive and preserve existing tables/rows. Keep one migration owner when starting multiple processes. Back up media and database together; the local filesystem stores photo originals, normalized images, and per-attempt analysis artifacts.

## Sensor processing

`Sensor/Sensor.ino` reads SGP41 VOC/NOx channels and BME280 temperature, humidity and pressure from an ESP32-S3. It publishes JSON to AWS IoT Core with certificate-based MQTT authentication.

The cloud rule routes telemetry to SQS and S3. The inference worker validates identifiers/ranges/sequences, creates device-isolated sessions, filters gas signals, establishes a baseline, computes biochemical and cumulative thermal heuristics, detects state changes, and estimates time to a configured risk threshold. Temperature parameters are in `config/food_types/`.

The worker writes raw local JSONL, database readings, complete snapshots, and transition events. Configured SNS alerts have a per-device cooldown. The HTTP `/telemetry` endpoint runs the same inference/persistence path; its SSE endpoint pushes HTTP-ingested results. The dashboard polls stored status every four seconds, including readings produced by the separate SQS worker.

The dashboard discovers device IDs from recorded sessions. Empty feeds display a waiting state, disconnected feeds retain their last readings, and chart timestamps come from ingestion. Baseline and thermal integration state live in process memory and begin a new session after a worker restart.

## Source map

- `frontend/`: React views, API client, styling, static assets, Vite configuration.
- `src/backend/api/`: product and sensor HTTP entry points and endpoints.
- `src/backend/meta/`: Meta client, segmentation parser, visual evidence and planning adapters.
- `src/backend/workflows/`: durable perception job processing.
- `src/backend/contracts/`: input/output schemas and evidence categories.
- `src/backend/{ingestion,processing,biochemical,thermal,detection,rul,fusion,evidence}/`: sensor pipeline.
- `src/backend/persistence/`, `storage/`: schemas, migrations, repositories and media.
- `Sensor/`: firmware, wiring and example device configuration.
- `scripts/`: launchers, offline replay, evaluation, model validation, deployment and diagnostics.
- `data/fixtures/`: attributed sample photos and explicitly labeled fixture sessions.
- `demos/video-model-flow/`: self-contained recorded model lab.
- `docs/validation/`, `docs/media/`: saved experiment results and walkthrough evidence.
- `tests/`: offline model-boundary, API/storage, migration and sensor regression checks.
- `config/{policies,prompts,protocols}/`: design extension points documented in their READMEs.

## Operational boundaries

Local APIs bind to loopback and are intended for a controlled development machine. Batch scoping enforces referential integrity; it is not user authentication. Public deployment needs authentication, authorization, reviewed IAM/network rules, HTTPS, and a coordinated migration/worker strategy.

Photo observations and sensor sessions remain separate evidence streams. Sensor-to-batch linking, an interactive Wonder planner, and a complete stock-action workflow are roadmap items. Inspection categories and modeled risk estimates do not establish food safety or calibrated expiry times. The [audit](repository_audit.md) separates automated verification from live provider/hardware/cloud checks.
