# Phased implementation plan

Prepared: 2 November 2026. Product name: undecided.

Implementation status: Phase 1, Phase 2's capture/history slice and Phase 3's durable
jobs, real item-level SAM/Spark pipeline, overlays, public samples and review storage
are now implemented on `codex/meta-model-validation` and live-tested. See
[visual prototype](visual_prototype.md). Independent accuracy evaluation is still
pending. Phase 4 sensor characterization/session integration is the next build gate.

## Outcome and starting point

Build one product that helps a user inspect a produce batch, investigate uncertain
evidence, confirm an action and return to its saved history. Rescue is the priority
queue, Investigator is the guided follow-up branch, and ShelfWatch is the shared
batch memory. They use the same records and workflow, rather than separate apps.

SAM, Spark, Wonder and voice have completed a recorded integration demonstration.
That replay is not the application or an accuracy benchmark. The existing device
dashboard and telemetry pipeline remain the starting implementation. Most product
directories are scaffolding. See [architecture](repository_architecture.md),
[model report card](model_report_card.md) and [testing roadmap](testing_roadmap.md).

Mixed-tomato image discovery and collection are deferred until the capture path is
ready. Foundation work can use explicitly labeled fixtures and the existing demo
image; fixtures must never be presented as new live inference or measured accuracy.

## Delivery order

| Phase | Deliverable | Dependency |
| --- | --- | --- |
| 1 | Durable batches, evidence contracts and media storage | Start now |
| 2 | Batch registration, capture and saved history in the app | Phase 1 |
| 3 | Real item-level SAM/Spark inspection | Phase 2; select images here |
| 4 | Valid, batch-linked sensor sessions | Contract work after Phase 1; hardware trials can begin alongside Phases 2–3 |
| 5 | Inspection priority and confirmed actions | Phase 3; validated sensor evidence from Phase 4 for combined scoring |
| 6 | Wonder follow-up, Investigator and due checks | Phase 5 |
| 7 | Independent evaluation and release | Working end-to-end path |

These are completion gates, not claims that earlier calendar deadlines were met.
Do not assign a fixed delivery date until the first implementation slice and
sensor trials establish the remaining effort.

## Phase 1 — Data foundation: the next implementation task

**Build:** explicit batch identity, durable evidence links and recoverable storage.

1. Review current database initialization and choose one ordered migration mechanism.
   Preserve existing telemetry records; make development database selection explicit.
2. Add typed contracts for Batch, Observation, MediaAsset and SensorSession links.
   Define quantity units, UTC timestamps, lifecycle states and validation errors.
3. Add migrations and transactional repositories. Use UUIDs; a device ID is not a
   batch ID. Define deletion/retention behavior for referenced evidence.
4. Add local media storage behind a replaceable interface: validate type/size,
   preserve original bytes, normalize a derived image, hash assets and keep uploads
   outside public source directories. Validate decoded dimensions as well as bytes.
5. Add batch create/list/detail and observation-history API routes. Register routers
   before the static frontend catch-all. Keep secrets server-side.
6. Add the minimum model-call metadata contract: model/prompt version, response ID,
   usage, latency, status and evidence references. An error must remain an error.

**Destinations:** `src/backend/contracts/`, `persistence/`, `storage/`,
`api/endpoints/batches.py`, `api/endpoints/observations.py` and `workflows/batches.py`.

**Completion gate:** create a batch, attach a fixture observation, restart the API
and retrieve the same records and asset. Invalid IDs and cross-batch references
are rejected. Run migration and repository integration checks on a disposable DB;
verify existing telemetry records remain readable. No model calls are required.

## Phase 2 — First usable application slice

**Build:** register a batch → open its passport → upload a photo → see saved history.

- Extract a shared frontend API client with an explicit base URL and error handling.
- Add Batch Passport and Capture/Measure pages; preserve the current device view.
- Show upload, queued, running, complete and failed states. A refresh retrieves
  authoritative server state rather than creating another observation.
- Implement durable job status and bounded processing. Start with one worker and
  one deployment topology; do not rely on process-local state shared by assumption.
- Make repeated submissions idempotent, and let failed jobs be retried explicitly.

**Destinations:** `frontend/src/api/`, `pages/BatchPassport.jsx`,
`pages/CaptureMeasure.jsx`, capture components and observation workflows.

**Completion gate:** upload an allowed image, refresh/restart and recover the same
observation. A rejected upload or processing failure has a readable recovery path.
This phase can run with clearly marked fixture outputs; it is not live perception.

## Phase 3 — Item-level perception

**Build:** image → SAM masks → contextual crops → Spark observations → saved overlay.

1. Select or collect mixed-tomato images with documented permission and provenance.
   Begin with a shallow single-layer tray. Set aside independent batches for testing.
2. Reuse the tested SAM adapter; save mask geometry, source dimensions and
   image-local object IDs. Preserve the original image and rendered artifacts.
3. Generate each object's crop with surrounding context. Ask Spark for structured
   visible evidence, visibility limits and `inspect`, `no_visible_concern` or `unclear`.
   A category must reference its object ID; reject missing/unknown IDs.
4. Render clickable masks and observations. Allow human confirmation/correction;
   retain original model output separately from the human amendment.
5. Handle no objects, overlap, partial visibility, timeout and malformed output.
   Save prompt/model versions and call receipts; avoid repeat calls on page refresh.

**Destinations:** existing `meta/segmentation.py` and `meta/vision.py`, observation
contracts/workflow, storage artifacts and frontend capture/evidence components.

**Completion gate:** a real multi-tomato image produces persisted per-item results
and an inspectable overlay. A hidden surface remains uncertain. Object IDs are
image-local and are not assumed to track tomatoes after rearrangement. This proves
the workflow; independent labeled evaluation in Phase 7 establishes performance.

## Phase 4 — Sensor sessions and physical feasibility

**Build:** reserve device → baseline → sample → recovery → valid/invalid summary.

- Add durable device reservation and explicit batch/session attribution across the
  API and SQS worker. Reject overlapping sessions and ambiguous packet ownership.
- Record actual sampling times, raw signals, processed indices, temperature,
  humidity, phase boundaries and packet gaps. Review firmware sampling continuity.
- Characterize empty, visually normal, deteriorated and mixed conditions with a
  fixed setup. Follow the detailed controls in the testing roadmap.
- Version the protocol after pilot trials establish stability/recovery rules.
  Return validity reasons and numerical summaries, not a food-safety conclusion.
- Show disconnected, stale, unstable and missing evidence explicitly. Remove
  fabricated nominal readings and unsupported remaining-life claims from this flow.

**Destinations:** session contracts/workflows, ingestion, processing, persistence,
`config/protocols/`, session endpoints and SessionProgress UI.

**Completion gate:** a session belongs to exactly one batch; invalid sessions cannot
update its priority. Save the written protocol and raw trial log. If sensor
conditions cannot be distinguished reproducibly, retain a camera-led product and
show the sensor as experimental. Group-localization remains disabled.

## Phase 5 — Rescue priority and action closure

**Build:** evidence comparison → inspection queue → human-confirmed outcome.

- Implement versioned deterministic policy, evidence-age checks and disagreement
  rules in code. Display camera-only, sensor-only and combined evidence separately.
- Treat the PDF's proposed weights as uncalibrated design candidates. Enable a
  combined score only after its required inputs and mapping are supported by trials.
  Missing evidence must not become zero or silently receive redistributed weights.
- Prioritize unresolved concerns and acquisition tasks; retain visual concerns
  even when the sensor is quiet. Use inspection language, not safety certification.
- Save confirmed quantities/actions transactionally with actor, time, evidence IDs
  and an idempotency key. Prevent duplicate or excessive quantity changes.
- Render Today, Decision/Action and the updated batch timeline.

**Completion gate:** the same evidence yields the same versioned decision; an
offline sensor is visibly unavailable; a confirmed removal appears once in history
and changes the quantity once. The user can compare pre/post evidence without an
automatic claim that the remaining produce is fresh.

## Phase 6 — Investigator, Wonder and ShelfWatch follow-up

**Build:** a bounded next step that persists and can be completed later.

- Extend Wonder's tested read-only loop with allowlisted history/protocol lookup
  and task proposals. Backend code validates batch IDs, permissions and transitions.
- Support another view, repeat a valid measurement, human inspection and stop as
  unresolved. Enforce test/time budgets and preserve interrupted task state.
- Add persistent due checks, completion records and evidence receipts. A return
  visit must show the same open task and its supporting history.
- Enable controlled group comparisons only if physical feasibility passes. Keep
  balanced groups, recovery requirements and inconclusive outcomes explicit.
- Add optional voice after the typed workflow is reliable; confirmation remains
  necessary for stock actions. Versioned protocol lookup can precede vector RAG.

**Completion gate:** Wonder uses real stored evidence, cannot bypass invalid
measurements, and produces a task that survives restart. Test conflicting evidence,
tool failures, unknown batch IDs and exhausted budgets. Models never directly
authorize disposal or alter the quantity ledger.

## Phase 7 — Evaluation and release

**Build:** a credible report card and a reproducible end-to-end demonstration.

- Freeze prompts, policy and protocol before held-out testing. Split by physical
  batch, not adjacent frames; label reference items without seeing predictions.
- Measure SAM IoU/Dice and missed objects; Spark confusion matrix, concern recall,
  false alarms and unclear rate; Wonder task completion/protocol violations; voice
  WER and critical ID/quantity errors if voice ships. Include sample counts.
- Compare image-only, sensor-only and combined decisions on the same cases.
  Report wrong and unresolved results, task time, API failures, cost and latency.
- Run targeted removal, normal-item removal and sham controls before making a
  sensor-improvement claim. Keep raw trial evidence, including failed runs.
- Test database recovery, a clean install, frontend build, phone capture, access
  controls, restricted origins and server-only keys before external deployment.
- Record the actual application flow and distinguish recordings/replays from new
  inference. Update setup, architecture status and measured limitations.

**Completion gate:** a new user can complete capture → inspection → valid session
or explicit missing evidence → confirmed action → follow-up. Publish measured
metrics with denominators; choose performance acceptance thresholds before testing.
Use observed errors to decide whether prompts, capture, retrieval or training need
improvement. Do not assume fine-tuning support for the hosted endpoints.

## Implementation discipline

Use a `codex/` feature branch for each reviewable milestone. Keep commits focused
on contracts/storage, API/workflow and UI where those changes can stand separately.
Run checks appropriate to each slice and update architecture labels from planned
to implemented only after its gate passes. Push/merge when authorized; keep keys,
private captures, local databases and raw caches out of Git.

**Start next:** Phase 4 sensor-session contracts and hardware characterization,
alongside independent item labels for Phase 3 evaluation. Do not add training/RAG
before a measurable baseline exists.
