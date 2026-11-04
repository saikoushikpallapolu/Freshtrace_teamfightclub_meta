# Visual inspection prototype

Current local visual inspection workflow. See [setup](setup.md) for complete installation, environment configuration, and dashboard ports.
This is a functioning local visual-inspection prototype, not a validated freshness
classifier or the complete sensor/agent product.

## What you can do

1. Register a batch and open its passport.
2. Upload a JPEG/PNG, or expand **Try a real public sample photo** and import one.
3. Open that observation and choose **Analyse tomatoes**. This makes live paid
   Meta calls; importing, viewing, filtering and reopening saved results do not.
4. See inspection flags, unclear items, a SAM overlay and image-local item IDs.
   Select the actual tomato on the image or use its numbered button. Switching
   between original/overlay and categories does not call models.
5. Read the contextual crop, visual observations and visibility limits. Expand the
   review form to confirm/correct an item with a note. Model output is retained;
   reviews are appended separately. This does not remove stock or update quantity.
6. Return to the same URL and see the saved result, review and model receipts.

The batch used for development is labeled **Public photo tests · quantity
illustrative**. Its photographs are unrelated source scenes grouped for UI testing,
not successive captures of a real physical batch. Do not interpret the registered
quantity or sample timestamps as measured produce inventory/capture dates.

## Start the prototype

From the repository root, using Python 3.12:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev,models]"
.venv\Scripts\python.exe scripts/run_product.py --ask-key
```

The launcher also reads `MODEL_API_KEY` from root `.env`. With `--ask-key`, enter the key at the hidden terminal prompt. It is held in process memory,
never saved or sent to the browser. Alternatively, provide `MODEL_API_KEY` through
the process environment and omit `--ask-key`. Do not paste the key into source,
the frontend or Git. Startup makes no model calls unless previously queued jobs
exist and the key is configured; those jobs resume as described below.

In another terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. The API listens only on loopback port 8080. Database
and media defaults remain `product_local.db` and `data/media/uploads`. Set
`PRODUCT_DATABASE_URL`/`PRODUCT_MEDIA_ROOT` before starting to use another local
database/media pair. Database and media locations can be overridden independently in `.env`; back them up together.

Without a key, batch/photo/history and public imports work, but new live analysis
is disabled. The original combined telemetry API also exposes the product routes,
but its embedded perception worker is intentionally disabled: use the standalone
product entry point for this local prototype.

This build has no tenant authentication. Keep it on loopback; do not expose it as
a public service. PostgreSQL, distributed workers and deployment remain unverified.

## Model and job flow

```text
Saved observation -> unique durable job -> atomic worker claim
  -> orient/normalize saved pixels -> resize analysis image to at most 1280 px
  -> SAM 3.1 -> validate and decode geometry/masks
  -> at most 32 candidate regions -> contextual crops with target rectangles
  -> one Muse Spark 1.3 structured request (scene + all target crops)
  -> validate exact IDs/categories -> save evidence, overlay and pixel-picking map
  -> completed observation -> user review and bounded next-step guidance
```

SAM returns geometry, not rotten/fresh categories. Spark records visible evidence,
not sensor chemistry or remaining life. Models do not authorize stock disposition.
The prototype's next-step text is deterministic code, not a Wonder output.
Wonder scheduling, optional voice and sensor-session execution remain later work.

Successful jobs make at most two model requests. A failed SAM stage can consume a
request without yielding an inspection. There are no automatic provider retries.
Repeated start requests reuse the same observation's job; explicitly retrying a
failed job creates a new numbered attempt and can spend credits again. All returned
call receipts are retained, including earlier attempts. A succeeded receipt means
the provider response completed, not that the overall job or its interpretation
was correct.

Queue state is durable. Atomic conditional claims prevent two local workers from
processing the same attempt. Queued jobs resume on startup when credentials are
configured. Running jobs interrupted by a process exit remain leased for up to 15
minutes, then become failed with `worker_interrupted`; they are not silently billed
again. This is a single-process local prototype, not a production distributed queue.

Geometry, crop/result validation and rendering happen before the result becomes
available. Empty masks, incomplete/invalid responses, wrong item IDs, missing files,
unknown batches and cross-batch evidence do not become a reassuring inspection.
More than 32 regions produces an explicit smaller-group/crop request. Image regions
can include partial fruit or erroneous detections; region count is not inventory.

Image picking uses a saved mask-pixel ID map, rather than overlapping rectangles.
Numbered controls support keyboard selection. Original pixels, derived artifacts,
the job result and reviews remain linked to the observation. Human edits do not
repaint or overwrite the original model classification.

## Real exploratory run

Three public source photographs and one explicitly derived spatial crop were run.
Source attribution, licences, original hashes and crop bounds are in the
[sample manifest](../data/fixtures/tomato_images/manifest.json). No scenes were
generated or composited. These are development examples, not independent test sets.

| Input | Outcome | Inspect | No visible concern | Unclear |
| --- | --- | ---: | ---: | ---: |
| JIP, mixed mold/normal-looking surfaces | 28 regions, complete on attempt 2 | 4 | 10 | 14 |
| Gideon, damaged market tomatoes | 2 regions, complete | 2 | 0 | 0 |
| George Chernilevsky, full basket scene | Stopped above the 32-region bound | — | — | — |
| Same basket, disclosed detail crop | 24 regions, complete | 5 | 11 | 8 |

The mixed-photo first attempt stopped at the original 24-region bound after SAM
returned 28 regions. Capacity was revised to 32, then explicitly retried; the first
call is preserved. The full basket's failure was not erased or relabeled as success.
The crop is a different input and is correlated with the full image.

On the mixed image, Spark highlighted prominent white filamentous patches (T11 and
T22) and wrinkled/depressed surfaces (T02 and T07). Several tiny or gap-like SAM
regions became unclear. These observations suggest useful visible evidence and
also expose segmentation/visibility limitations. Basket flags include surface
damage/scars/creases; they are not five independently confirmed rotten tomatoes.

No reference masks or independent item labels exist, so IoU, precision, recall,
F1 and food-quality accuracy remain unmeasured. Three completed inputs and one
guarded input are workflow outcomes, not a model accuracy percentage. The saved
UI-test review explicitly says it is not independent human/physical inspection.

Evidence: [full saved results and receipts](validation/prototype_results.json),
[mixed overlay](assets/prototype_mixed_mold_overlay.jpg),
[damage overlay](assets/prototype_market_discard_overlay.jpg),
[basket-detail overlay](assets/prototype_basket_detail_overlay.jpg),
[browser proof](assets/prototype_inspection_ui.png).
Mixed derivatives/screenshots retain JIP's CC BY-SA 4.0 licence; damaged-photo
derivatives retain Gideon's CC BY-SA 2.0; basket derivatives credit George
Chernilevsky under CC BY 4.0. Licence/source links are also displayed in the app.

## Verification and reproduction

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=tmp/prototype-tests-local
cd frontend
npm run build
npm run lint
```

Use a disposable pytest base directory. Recorded result: **30 tests passed**,
new Python files passed Ruff, production frontend build passed, and lint warnings
were confined to the pre-existing device dashboard. Tests cover migration/model
consistency and legacy preservation, media boundaries, durable retries, queued-job
restart, failures and explicit retries, two-worker claims, append-only reviews,
cross-batch access, exact object IDs and mask-pixel picking. Offline tests inject
clearly identified fixtures and make no Meta/AWS calls.

Browser checks covered sample import, actual paid analysis, flag filtering,
numbered/keyboard selection, mask-based pointer selection, saved UI-test review and
reload without new inference. Existing stored results survived API restarts.

For new paid runs, with the API running and an existing test batch:

```powershell
.venv\Scripts\python.exe scripts/evaluation/validate_prototype.py --live --batch-id YOUR_BATCH_UUID
```

This imports samples, starts/reuses their jobs, checks artifacts and saves sanitized
results to `tmp/prototype_validation.json`. A guarded/failed input produces a nonzero
exit status. It does not automatically retry that job. Use `--samples basket_detail`
to run the separate detail crop. Actual usage/billing remains provider-authoritative.

## Next gates

1. Independently label new physical trays and measure missed objects, false flags,
   unclear rate and visible-concern recall. Keep these development photos out of a
   future held-out test set. Add capture/prompt improvements only against recorded errors.
2. Characterize the sensor procedure and implement durable batch/session attribution,
   device reservation, phase timestamps, validity and missing-state behavior.
3. Add conservative policy and confirmed quantity actions, then Wonder's bounded
   follow-up tools and persistent due checks.
4. Run controlled removal versus normal-removal and sham-handling arms. A falling
   sensor graph alone must not be called proof that affected items were removed.

RAG or fine-tuning is not a prerequisite for this prototype; neither substitutes
for reference labels or a reproducible physical measurement protocol.
