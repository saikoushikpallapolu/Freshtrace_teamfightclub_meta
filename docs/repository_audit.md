# Repository audit

Audit date: **4 November 2026**. Scope: frontend, product and sensor APIs, contracts, persistence/migrations, Meta adapters, perception jobs, firmware, replay/evaluation/deployment scripts, environment configuration, and setup documentation.

## Repairs

- Replaced the introductory README with a project overview, dashboard/port map, Windows quick start, architecture diagram, and links to the current guides.
- Consolidated startup instructions in `docs/setup.md`, covering Windows/macOS/Linux, environment configuration, hardware, AWS, verification, and troubleshooting.
- Added explicit product/sensor/worker launcher modes: APIs use 8080 and 8081, the frontend uses strict port 5173, and the model lab uses 8767.
- Completed the environment template, kept keys server-side, and ignored environment variants, packaging metadata, local endpoint records, test coverage and research cache output.
- Connected the sensor UI to discovered device IDs and stored inference results. Removed unused scenario handlers and initial sample metrics/charts; added a waiting state, measured update age, duplicate chart-point handling, and device selection.
- Corrected the hardware display to SGP41 + BME280 and replaced unsupported outcome claims with descriptions of observed/configured behavior.
- Added complete persisted sensor snapshots through migration `0004_sensor_snapshot`, preserving existing rows and keeping missing historical components unavailable.
- Fixed the fallback telemetry timestamp field, unique session IDs, duplicate/out-of-order packet rejection, identifier path validation, finite-number validation, calibration completion state, and zero-duration thermal exposure handling.
- Rolled back in-memory calibration/sequence state on failed writes and propagated persistence failures instead of reporting success and dropping a queue message after a failed write. Alert cooldown starts only after a successful publish.
- Bounded SSE queues and cleaned up disconnected subscribers. Limited history query size and sensor CORS origins.
- Restored the standard AWS credential chain for IAM roles and session tokens, removed a fixed cloud diagnostic instance identifier, stopped printing generated database passwords, required trusted network ranges for new cloud ingress, implemented the existing-instance update path, and made cloud verification fail when the submitted packet is not observed.
- Applied consistent Python formatting/import cleanup and removed unused frontend imports and handlers.

## Verification

The automated suite covers batch persistence/restart, migrations and legacy-row preservation, image orientation/original integrity, invalid/oversized uploads, cross-batch constraints, retry receipts, durable job claiming, sanitized failures and explicit retry, model request/response contracts, exact-mask selection, human review persistence, device isolation, complete sensor snapshots, legacy snapshots, empty feeds, identifiers/sequences, calibration, and thermal timing.

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=tmp/verification
.venv\Scripts\python.exe -m ruff check src/backend scripts tests
.venv\Scripts\python.exe -m ruff format --check src/backend scripts tests
npm --prefix frontend run build
npm --prefix frontend run lint
```

Tests use disposable storage and controlled provider responses. Model credentials are not required and provider/cloud requests are not made by the suite. Production builds and static checks verify the client bundle and source; local HTTP checks verify frontend/API routing. Verified on Windows with Python 3.13.6 and Node.js 22.17:

| Check | Result |
| --- | --- |
| Offline test suite | 40 passed; one third-party TestClient deprecation warning |
| Python lint | Passed |
| Python formatting | 94 files passed |
| Frontend production build | Passed |
| Frontend lint | Passed with no warnings |
| Markdown local links | 33 files checked; no missing targets |
| Local HTTP routes | Visual/sensor APIs, frontend views, and Vite proxy routes responded successfully |

An automated visual browser walkthrough could not be completed in this session; HTTP checks do not substitute for visual layout testing.

## Deployment and validation boundaries

The supplied startup flow is for loopback development. Authentication/tenant authorization, coordinated multi-process migrations and distributed worker operation require additional implementation before public deployment. AWS provisioning scripts operate on real resources and need reviewed IAM/network/HTTPS configuration; pre-existing security-group rules must be reviewed separately. No cloud deployment or billable provider run is performed by this audit.

Previously recorded model-validation artifacts remain attributed experiment evidence; this audit does not replace them with a new accuracy result. Sensor baseline/thermal state restarts with the worker, and photo batches are not automatically linked to sensor sessions. Physical repeatability, food-safety validity, calibrated shelf-life accuracy, SNS delivery and AWS resource health require their own live checks.
