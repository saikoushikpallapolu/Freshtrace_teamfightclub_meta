# Repository architecture and implementation map

Reviewed: 31 October 2026. Product name: undecided.

This document describes the actual repository and a complete target layout for
the combined Rescue, Investigator and ShelfWatch workflow. Existing application
files stay in place. New directories contain documentation only; filenames shown
as planned below are implementation destinations, not working features.

### Model-validation branch update - 1 November 2026

On `codex/meta-model-validation`, `src/backend/meta/{__init__,client,vision,segmentation,planner}.py`
and `tests/unit/test_meta_integration.py` are now implemented. The standalone
`scripts/smoke/validate_meta_models.py` exercises real hosted inference and a
fixture-backed, read-only history tool. See [model validation](model_validation.md)
for the run evidence. The target tree below retains the original planning labels
as the baseline; these named files are the exception. Product endpoints, persistence
migrations, task orchestration and UI wiring are still planned.

## 1. Architecture at a glance

The existing application is device-centered. The proposed product is batch-centered:
one batch owns a history of photos, sensor sessions, decisions and confirmed
outcomes. A sensor is a reusable instrument that can measure different batches.

### Current runtime, as read from source

```text
ESP32-S3 + BME280 + SGP41
  -> MQTT/TLS -> AWS IoT Core
                  -> rule -> S3 raw archive
                  -> rule -> SQS
                               -> backend.inference_service (worker process)
                                  -> ingestion + signal processing
                                  -> biochemical / thermal / onset / RUL / fusion
                                  -> SQLAlchemy -> PostgreSQL or SQLite
                                  -> optional SNS alert

HTTP POST /telemetry -> FastAPI's separate InferenceEngineService instance
                         -> same processing/persistence pipeline
                         -> process-local SSE subscriber queues

React App.jsx -> HTTP status/history polling -> FastAPI -> database/latest state
```

Cloud arrows describe what provisioning/deployment scripts configure; deployment
health, live hardware and cloud resource state were not verified during this review.
The browser currently polls status/history; the backend also exposes an SSE route.

### Target product flow

```text
React: Today -> Batch Passport -> Capture/Measure -> Investigate -> Confirm action
   -> FastAPI endpoints + typed contracts
      -> workflows: task state, sensor protocol, priority policy, outcomes
         -> meta adapters: SAM segmentation / Spark observations / Wonder planning
         -> storage: original photos, decoded masks, raw-session references
         -> persistence: batches, observations, sessions, tasks, decisions, outcomes
         -> existing telemetry pipeline: validated sensor-session summaries
   <- saved evidence, validated decisions, next check and readable receipts
```

The database owns workflow state. Code owns measurement validity, arithmetic,
scoring and authorization. Models propose interpretations and allowed next steps.
Only a human confirms stock disposition. No model is called per telemetry packet.

## 2. Complete repository layout

Legend: `[existing]` is already implemented or present; `[scaffold]` is a new
documentation-only directory. Children marked `[planned]` do not exist yet.
Folders may contain a README rather than executable placeholders so unimplemented
features cannot accidentally be imported or treated as available.

```text
meta_2026/
|-- README.md                          [updated] project overview and document links
|-- .env.example                       [existing] environment template; extend later
|-- .gitignore                         [existing + artifact exclusions]
|-- pyproject.toml                     [existing] package metadata, pytest/ruff config
|-- requirements.txt                   [existing] runtime requirements, currently incomplete
|
|-- docs/
|   |-- product_build_plan.pdf         [new] product-neutral strategy and delivery plan
|   |-- repository_architecture.md     [new] this architecture map
|   `-- Strategy.md                    [existing working-tree document; not rewritten]
|
|-- Sensor/                            [existing; preserve case and sketch location]
|   |-- Sensor.ino                     ESP32-S3 sampling, compensation and MQTT/TLS
|   |-- secrets.example.h              safe firmware settings template
|   `-- README.md                      hardware, wiring, payload and setup
|   # secrets.h is private and ignored
|
|-- config/
|   |-- food_types/                    [existing] tomato.json and paneer.json
|   |-- protocols/                     [scaffold] versioned sampling/validity settings
|   |   `-- tomato_v1.json             [planned]
|   |-- policies/                      [scaffold] inspection-priority policy settings
|   |   `-- inspection_v0.json         [planned]
|   `-- prompts/                       [scaffold] versioned observation/planning prompts
|       |-- visual_observation_v1.md   [planned]
|       `-- next_action_v1.md          [planned]
|
|-- src/
|   |-- __init__.py                    [existing]
|   `-- backend/
|       |-- __init__.py                [existing]
|       |-- config.py                  [existing] application settings
|       |-- inference_service.py       [existing] pipeline orchestration / SQS worker
|       |-- api/
|       |   |-- __init__.py            [existing]
|       |   |-- routes.py              [existing] FastAPI app and current routes
|       |   `-- endpoints/             [scaffold] new APIRouter modules
|       |       |-- batches.py         [planned] batch CRUD and history
|       |       |-- observations.py    [planned] upload/capture and perception job status
|       |       |-- sessions.py        [planned] reserve/start/complete sensor sessions
|       |       |-- investigations.py  [planned] allowed tests and state advancement
|       |       |-- plans.py           [planned] daily plans and due tasks
|       |       `-- outcomes.py        [planned] human confirmation and receipt retrieval
|       |-- contracts/                 [existing] validated boundary data
|       |   |-- __init__.py
|       |   |-- baseline.py            existing baseline statistics
|       |   |-- telemetry.py           existing RawTelemetry schema
|       |   |-- processed.py           existing processed-reading schema
|       |   |-- session.py             existing session schema
|       |   |-- state.py               existing state schema
|       |   |-- events.py              existing evidence-event schema
|       |   |-- batch.py               [planned] batch identity and quantity units
|       |   |-- observation.py         [planned] photo/mask/visible-evidence schema
|       |   |-- decision.py            [planned] versioned priority + evidence status
|       |   |-- investigation.py       [planned] groups, tests and stop state
|       |   |-- task.py                [planned] next action, due time and completion
|       |   `-- outcome.py             [planned] human-confirmed disposition
|       |-- ingestion/                 [existing] processor.py + __init__.py
|       |-- processing/                [existing] signal_processor.py + __init__.py
|       |-- biochemical/               [existing] engine.py + __init__.py
|       |-- thermal/                   [existing] engine.py + __init__.py
|       |-- detection/                 [existing] onset.py + __init__.py
|       |-- rul/                       [existing] estimator.py + __init__.py
|       |-- fusion/                    [existing] risk.py + __init__.py
|       |-- evidence/                  [existing] events.py + __init__.py
|       |   `-- receipts.py            [planned] redacted/versioned receipt export
|       |-- persistence/               [existing] database ownership
|       |   |-- __init__.py
|       |   |-- db.py                  connection/session creation and schema initialization
|       |   |-- models.py              existing Session/Telemetry/Event/State tables
|       |   |-- repositories.py        [planned] workflow queries and transactions
|       |   `-- migrations/            [scaffold] ordered schema evolution; runner undecided
|       |-- meta/                      [scaffold] hosted model adapters only
|       |   |-- client.py              [planned] auth, timeout, retry, usage and response IDs
|       |   |-- segmentation.py        [planned] SAM request/parser/geometry normalization
|       |   |-- vision.py              [planned] Spark evidence extraction and explanation
|       |   |-- planner.py             [planned] Wonder allowed-tool loop
|       |   `-- transcription.py       [planned, optional] voice-to-text adapter
|       |-- workflows/                 [scaffold] product rules and orchestration
|       |   |-- batches.py             [planned] register batch and link observations
|       |   |-- sessions.py            [planned] device lock, phases and validity
|       |   |-- policy.py              [planned] deterministic inspection priority/gates
|       |   |-- investigation.py       [planned] bounded retest and optional A/B state
|       |   |-- tasks.py               [planned] due checks and allowed agent tools
|       |   `-- outcomes.py            [planned] human confirmation and quantity ledger
|       |-- storage/                   [scaffold] local/cloud object-store boundary
|       |   |-- media.py               [planned] hash/orient/store original photos
|       |   `-- artifacts.py           [planned] masks and raw-log references
|       `-- evaluation/                [scaffold] reusable offline evaluation logic
|           |-- ablation.py            [planned] same-case camera/sensor/combined runs
|           |-- investigation.py       [planned] blinded group comparison metrics
|           `-- longitudinal.py        [planned] chronological scheduling comparisons
|
|-- frontend/
|   |-- package.json / package-lock.json  [existing] React/Vite tooling and lockfile
|   |-- vite.config.js                 [existing] React plugin; no dev proxy configured
|   |-- index.html                     [existing] HTML entry
|   |-- .gitignore / .oxlintrc.json     [existing] ignores and lint rules
|   |-- README.md                      [existing] frontend tooling notes
|   |-- public/                        [existing] static images/icons, served as paths
|   `-- src/
|       |-- main.jsx                   [existing] React mount
|       |-- App.jsx                    [existing] dashboard, data fetching and UI state
|       |-- App.css / index.css        [existing] current styling
|       |-- assets/                    [existing] imported images/icons
|       |-- api/                       [scaffold]
|       |   |-- client.js              [planned] shared base URL and error handling
|       |   |-- batches.js             [planned] batch/history requests
|       |   `-- tasks.js               [planned] sessions, plans and confirmations
|       |-- pages/                     [scaffold]
|       |   |-- Today.jsx              [planned] queue and due checks
|       |   |-- BatchPassport.jsx      [planned] history and receipt access
|       |   |-- CaptureMeasure.jsx     [planned] photo and sensor protocol
|       |   |-- Investigation.jsx      [planned] retest / A/B / unresolved paths
|       |   `-- DecisionAction.jsx     [planned] evidence comparison and approved action
|       |-- components/                [scaffold]
|       |   |-- capture/               [scaffold] CameraCapture, MaskOverlay, SessionProgress
|       |   |-- evidence/              [scaffold] PriorityComparison, EvidenceTimeline, Receipt
|       |   `-- shared/                [scaffold] status, loading, errors and confirmations
|       `-- hooks/                     [scaffold] useBatch, useDeviceStatus, useTask
|
|-- data/
|   |-- README.md                      [new] provenance and storage rules
|   |-- tomato_fresh_data.csv          [existing] source data; verify provenance before claims
|   |-- tomato_rotten_data.csv         [existing] source data; verify provenance before claims
|   |-- tomato_master_dataset.csv      [existing] derived/master data; provenance not verified
|   |-- fixtures/                      [existing] valid/bad sessions + synthetic master CSV/JSONL
|   |-- evaluation/                    [scaffold] sanitized evaluation manifests and summaries
|   |   `-- runs/                      [runtime, ignored] generated per-run outputs
|   |-- raw/                           [runtime, ignored] local raw telemetry JSONL
|   |-- processed/                     [runtime, ignored] derived measurement outputs
|   `-- media/                         [scaffold] README only; local uploads/masks ignored
|
|-- scripts/
|   |-- deploy_aws_infra.py            [existing] IoT/SQS/S3/SNS/RDS provisioning
|   |-- deploy_aws_backend.py          [existing] backend bundle, EC2 and systemd services
|   |-- deploy_aws_frontend.py         [existing] Vite build, S3 and CloudFront
|   |-- wait_for_rds.py                [existing] database provisioning helper
|   |-- diagnose_realtime_pipeline.py  [existing] operational diagnostics
|   |-- verify_full_cloud_deployment.py [existing] cloud verification
|   |-- test_aws_e2e_pipeline.py       [existing] operational cloud test
|   |-- test_paneer_flow.py            [existing] existing scenario script
|   |-- replay_session.py             [existing] offline pipeline replay
|   |-- stitch_datasets.py            [existing] creates explicitly synthetic timeline data
|   |-- smoke/                        [scaffold] future Meta/API access checks
|   |-- evaluation/                   [scaffold] future CLI entry points for offline metrics
|   `-- docs/
|       |-- README.md                 [new] PDF generator usage and dependencies
|       `-- build_product_build_plan.py [new] reproducible PDF authoring source
|
`-- tests/                             [scaffold] pytest target already declared in pyproject
    |-- unit/                          [scaffold] pure policy/protocol/contract tests
    |-- integration/                   [scaffold] API/database/adapter boundary tests
    `-- e2e/                           [scaffold] complete product workflow scenarios
```

`__init__.py` files for new Python packages are intentionally deferred until those
packages contain implementation. Generated `output/`, `tmp/`, local databases,
private uploads, `.env`, firmware secrets, node_modules and dist are not source.
The approved PDF is the exception: it is versioned explicitly under `docs/`.
The existing local strategy rename is separate work and is not included in this
architecture commit; its final tracked name depends on that separate change.

## 3. Existing module responsibilities

| Module | Current responsibility | Product integration boundary |
| --- | --- | --- |
| `Sensor/Sensor.ino` | Reads BME280/SGP41, compensates measurements, connects to Wi-Fi and publishes MQTT/TLS telemetry | Keep firmware independent of model prompts and business actions; introduce explicit sampling-session metadata through a designed protocol |
| `ingestion/processor.py` | Validates packets, assigns an in-memory session/device, tracks sequence gaps, appends raw JSONL | Replace implicit device-only session attribution with durable batch/session linkage |
| `processing/signal_processor.py` | Per-session baseline, filters and signal derivatives | Expose numerical features to the session summary; do not treat startup calibration as produce validation |
| `biochemical/`, `thermal/`, `detection/`, `rul/`, `fusion/` | Existing heuristic scores, onset state and remaining-life estimates | Preserve code for review; do not relabel values as calibrated food-safety probabilities |
| `evidence/events.py` | Builds baseline/state evidence events | Extend with references to photo/session/model/policy records; add receipts separately |
| `inference_service.py` | Runs pipeline, persists snapshots/events, consumes SQS, optionally publishes SNS | Reuse transport/processing but separate product workflow decisions from per-packet inference |
| `persistence/db.py`, `models.py` | SQLAlchemy engine/sessions and existing tables | Add transactions and migrations for durable batch/task state |
| `api/routes.py` | App, lifecycle, telemetry/status/history/events/SSE and SNS endpoints; optional static frontend mount | Keep entry point; register new routers before the catch-all static mount |
| `frontend/src/App.jsx` | Existing device dashboard, polling, notifications and presentation | Extract gradually into pages/components/hooks; preserve functionality until replacement works |
| `scripts/` | Provisioning, deployment, replay and operational verification | Keep paths stable; add new smoke/evaluation entry points without moving current scripts |

## 4. New layer boundaries and dependency direction

```text
API endpoints -> workflows -> contracts + persistence/storage + model adapters
model adapters -> provider SDK + contracts (no endpoint imports)
workflows -> existing measurement summaries (no UI imports)
evaluation -> saved records + policy (offline; no deployment side effects)
React pages -> hooks/API client + presentational components
```

- **API:** validates request identity/authorization, delegates work and returns status.
  Do not move all business logic into endpoint functions.
- **Contracts:** defines validated request/result schemas. Keep model output and
  trusted code-derived measurements distinguishable.
- **Meta:** server-only hosted inference. Centralize credentials, model IDs,
  timeouts, bounded retries, usage logs and response IDs in `client.py`.
  SAM returns geometry; Spark records visible evidence; Wonder proposes allowed
  tool actions. Voice is optional. No model weights or API keys belong in frontend.
- **Workflows:** owns device reservation, protocol phases, persistent task state,
  evidence-age/conflict gates, deterministic priority and human confirmation.
  Investigator is a branch of this workflow, not a second service.
- **Persistence/storage:** database stores relationships/state; object storage stores
  original media and large artifacts. Database records reference immutable object
  versions/hashes. A QR points to an access-controlled or redacted batch view.
- **Config:** stores reviewed, versioned protocol/policy/prompt definitions.
  Store measured constants only after trials; README scaffolding is not calibration.
- **Evaluation:** runs comparisons on saved, labeled inputs without future leakage.
  Report wrong and unresolved cases as well as correct results.

## 5. Data ownership and proposed relationships

```text
Batch 1 -> many Observations -> MediaAsset + SAM masks + Spark output
Batch 1 -> many SensorSessions -> RawTelemetry + validated SessionSummary
Batch 1 -> many Investigations -> Groups + controlled TestSessions
Batch 1 -> many Decisions -> evidence IDs + policy version
Batch 1 -> many Tasks -> due time + allowed action + completion
Decision 1 -> many Outcomes -> actor + confirmed quantity/action
Task/Observation/Investigation -> ModelCall -> response ID + usage + latency
```

Use explicit `batch_id`, `session_id`, `observation_id`, `task_id` and
`investigation_id`. A device ID is not a batch ID. Use transactional quantity updates
and idempotency keys for confirmations. Keep original capture time, server receipt
time and measurement phase times separate. Image-local object IDs do not identify
the same tomato after rearrangement. Evidence receipts support traceability, not
certification of freshness or food safety.

## 6. Architecture review: gaps to resolve during implementation

These are source-review findings, not fixes performed by this scaffolding change.

| Finding in existing code | Consequence | Intended destination / next change |
| --- | --- | --- |
| API creates an `InferenceEngineService`; deployment runs a separate SQS worker | Each process has its own `last_known_state`, session trackers and SSE queues; worker updates do not broadcast through API memory | Persist current state/device sessions; use database polling initially or an explicit shared event transport later |
| Ingestion assigns one in-memory session per device with second-resolution IDs | No batch/group attribution; reset/collision concerns across devices/processes | `workflows/sessions.py`, contracts and DB migrations: durable UUID sessions and exclusive reservation |
| Raw logging uses `telemetry.__dict__` for a Pydantic model | Serialization bypasses the schema's normal dump API and will be fragile as typed fields evolve | Review `model_dump(mode="json")` during ingestion changes; test serialization then |
| No batch, photo, model-call, investigation, task or outcome tables | The planned product cannot be represented by device snapshots alone | New contracts, persistence models/repositories and migrations |
| Status API and frontend supply nominal readings, floors and remaining-life defaults when evidence is absent | Missing/old evidence can appear like a real current measurement | Explicit missing/stale/invalid states in policy, API and UI; preserve historical evidence timestamps |
| Existing alerts include strong spoilage/safety/disposal language | Claims exceed the proposed inspection-priority evidence | Review both `api/routes.py` and `inference_service.py` when introducing human-confirmed actions |
| DB setup calls `create_all`; SQLite selection depends on environment/engine construction | `create_all` is not a migration system; creating a PostgreSQL engine does not prove connectivity or guarantee runtime SQLite failover | Ordered migrations, explicit health checks and clear dev/cloud DB selection |
| Existing FastAPI CORS allows `*` with credentials; no application auth is apparent in inspected routes | Vendor data and mutation endpoints need an explicit access design | Restrict origins and authenticate batch/action routes before public use |
| `App.jsx` is a large component with inline fetching and defaults | Product screens and error handling will be hard to evolve consistently | Extract API client, hooks, pages and reusable evidence components incrementally |
| Frontend has URL heuristics; Vite has no proxy; cloud scripts use separate static hosting | Browser/API origin and HTTPS compatibility need explicit configuration | Consolidate frontend API base; prefer same-origin HTTPS or correctly configured HTTPS API/CORS |
| `pyproject.toml` advertises Python >=3.9 but contracts use `X | None`; dependencies differ from requirements.txt | Declared install compatibility and actual runtime imports differ | Choose/test a supported Python version and reconcile manifests; add SDK/parser dependencies when implementing adapters |
| `.env.example` uses `APP_ENV`, while settings expects `APP_ENVIRONMENT`; RDS/SQS/SNS/Meta fields are incomplete | A copied template cannot describe the full current/future deployment | Extend the environment contract after config decisions; use instance roles where appropriate |
| `stitch_datasets.py` advances time synthetically; dataset provenance is not established here | Stitched histories cannot prove longitudinal early-warning performance | Preserve synthetic labels; collect separate real dated evaluation observations |
| Operational scripts provision resources and some execute top-level actions | Importing/running them is not a harmless unit test | Leave them outside pytest collection; review separately before execution |

## 7. Environment, commands and operating boundaries

Existing API entry point (run from repository root with the intended environment):

```powershell
python -m uvicorn backend.api.routes:app --app-dir src --host 127.0.0.1 --port 8080
```

Existing worker entry point:

```powershell
$env:PYTHONPATH = "src"
python -m backend.inference_service
```

The worker reads SQS and may publish SNS if configured. Running the API also creates
an inference service and database initialization; these are not pure import checks.
The new scaffold is intentionally not wired to either entry point.

Frontend commands remain in `frontend/package.json`: `npm run dev`, `npm run build`
and `npm run lint`. Configure `VITE_API_BASE` for split hosting; it must never contain
credentials. A mobile camera flow will need HTTPS or an appropriate trusted local
development context on the phone. Do not introduce native Android tooling yet.

Proposed server settings when adapters are implemented: `MODEL_API_KEY`, a Meta
base URL, model IDs, explicit timeouts, task/tool budgets and media-store selection.
These are a planned configuration contract, not settings already consumed by code.

## 8. Implementation order and completion rules

1. Confirm hosted model access and the sensor protocol; record feasibility results.
2. Implement batch contracts, persistence/migrations and storage before more UI.
3. Build a real capture -> SAM masks -> Spark observation -> saved history slice.
4. Link controlled sensor sessions; add validity, missing-state handling and policy.
5. Add Today and decision/action flow, human confirmations and a quantity ledger.
6. Add Wonder's bounded tools, persistent due checks and evidence receipts.
7. Add Investigator repeat/photo/stop paths; enable A/B only after its feasibility gate.
8. Add chronological evaluation, same-case ablations and vendor task results.
9. Verify deployment and record the demo; optional voice follows reliability work.

Each directory README names its future responsibilities. Add executable files only
as each slice is implemented, and update this map when a planned file becomes real.
Do not claim a new folder is a completed feature. The PDF supplies the fuller
user-flow, scoring, delivery-hour and demo plan.

## 9. Scope of this repository change

Added: product-neutral PDF, reproducible PDF source, architecture map, directory
READMEs, root document links and generated-artifact ignores. Existing application
source, firmware, datasets, dependency versions and deployment behavior were not
refactored. No cloud provisioning, notification, model inference or live hardware
action was needed to review and document the architecture.
