# Product development: first working slice

Update: the [visual prototype](visual_prototype.md) now adds durable SAM/Spark jobs,
item evidence, exact-mask picking, public samples and separate reviews. The account
below documents the earlier storage milestone; its statements about pending model
jobs are historical. Use the visual-prototype guide for current startup commands.

Updated: 2 November 2026. Branch: `codex/meta-model-validation`.

## Working behavior

Create a batch with a quantity/unit, upload a JPEG or PNG and save a timestamped
observation. Reopen the batch via its URL or restart the API: its evidence history
remains. Original bytes are preserved; a derived JPEG is oriented and stripped of
metadata for display. The media API scopes retrieval to the owning batch.

Phase 1 is implemented. Phase 2's registration/capture/history slice is implemented.
Durable inference jobs, model results and human corrections remain Phase 3 work;
there is no artificial queued/complete state or simulated analysis. A captured
observation means only that a photo was saved. Sensor links and model receipts have
schemas but no execution endpoints yet. No model credits are consumed by this slice.

The existing device dashboard remains accessible at `/?view=device`. Use the
existing combined backend to operate it; the standalone product API intentionally
does not expose telemetry routes or initialize AWS clients.

## Run locally

From the repository root, create/activate your intended Python environment and
install `pip install -e ".[dev]"`. Python 3.12 was used for verification.

```powershell
$env:PYTHONPATH = "src"
$env:PRODUCT_DATABASE_URL = "sqlite:///product_local.db"
$env:PRODUCT_MEDIA_ROOT = "data/media/uploads"
python -m uvicorn backend.api.product:create_app --factory --host 127.0.0.1 --port 8080
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the backend on port 8080.
`VITE_API_BASE` can override the base for a deliberately configured deployment.
The local API does not load `.env` or infer RDS settings. The existing combined API
still loads `.env`, now honors explicit `DATABASE_URL`, and otherwise uses complete
RDS configuration or its existing local default. Failed configured databases do
not silently fall back to another database. Incomplete RDS configuration fails.

## Data and migrations

- `0001_product_foundation`: batches, media, observations, sensor links and model
  call metadata. Composite foreign keys reject a photo from another batch.
- `0002_request_receipts`: durable idempotency keys for batch creation, media upload
  and observation creation. Same key/input replays the original record; changed
  input returns HTTP 409. Header keys are UUIDs, with a separate operation namespace.
- Startup applies ordered Alembic upgrades. Existing legacy tables are retained;
  their `create_all` bootstrap remains separate from product schema evolution.
- Back up an existing database before deployment. Only SQLite was exercised here;
  PostgreSQL deployment/multi-process startup migration coordination is not yet
  verified. Run migrations with a single startup owner before scaling processes.
- Destructive downgrades and deletion endpoints are intentionally absent. Evidence
  references must remain intact. Unreferenced files after a failed database commit
  are retained; an explicit reviewed cleanup/retention job is future work.
- Local DBs, user uploads and preview data remain ignored by Git. Back up the media
  root and DB together. A missing file returns an unavailable response, not evidence.

## API outline

| Method | Path | Purpose |
| --- | --- | --- |
| POST / GET | `/api/batches` | Register / list batches |
| GET | `/api/batches/{batch_id}` | Batch passport |
| POST | `/api/batches/{batch_id}/media` | Raw image bytes, matching Content-Type |
| GET | `/api/batches/{batch_id}/media/{media_id}` | Asset metadata without filesystem paths |
| GET | `/api/batches/{batch_id}/media/{media_id}/content` | Normalized JPEG; `?variant=original` for original |
| POST / GET | `/api/batches/{batch_id}/observations` | Save / list timestamped captures |

List endpoints support `limit` (maximum 100) and `offset`. The current UI shows the
latest 100 batches and observations with that limit labeled. Uploads are bounded
while streaming to 10 MiB, decoded to at most 20 megapixels, and limited to still
JPEG/PNG. Capture times require a timezone and are normalized to UTC.

Use `/docs` on the API for request schemas. This is a loopback development build:
authentication, tenant ownership and external deployment are not implemented.
Batch scoping is referential integrity, not user authorization. Keep this local
until the access-control gate passes. No wildcard CORS is added to the new API.

## Verification

```powershell
python -m pytest tests -q --basetemp=tmp/product-tests-local
cd frontend
npm run build
npm run lint
```

The pytest base directory must be disposable: pytest may clear it on later runs.
The integration suite uses only temporary SQLite/filesystem storage, with no Meta
or AWS calls. It checks restart persistence, legacy-row preservation, schema/model
consistency, original-image integrity/orientation, invalid uploads, cross-batch
constraints, durable retry replay and conflicting retries. Model-adapter unit tests
remain part of the suite. API/browser tests need a functioning Windows event loop.

Recorded verification: 22 tests passed; new Python files passed Ruff; frontend
production build passed; lint exited successfully with warnings confined to the
pre-existing device dashboard. Compatible Vite/source-map dependency updates
reduced the npm audit result to zero advisories. A separate local smoke check
confirmed batch creation and health through the original API with AWS messaging
disabled. PostgreSQL and physical sensor behavior were not exercised.

Browser verification used the already checked-in Wikimedia demo frame, not a new
mixed-tomato dataset: register batch, upload/save photo, reload and see the same
record. [Screenshot](assets/product_batch_workspace.png). Source attribution and
CC BY-SA 3.0 terms are in the [demo guide](video_model_demo.md); the screenshot
contains a thumbnail derived from that source and is shared under those terms.

## Next implementation slice

Add durable perception-job state, connect real SAM/Spark calls to saved observations,
generate contextual item crops and persist masks/results/usage. Test the queue with
fixtures before paid calls. Then select mixed-tomato images and independently label
the item evidence. Do not turn this storage milestone into an accuracy claim.
