# Access smoke checks

## Run hosted Meta checks

For the complete tested adapter path (strict vision JSON, decoded SAM masks and
a bounded Wonder tool round trip), use Python 3.12 and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/smoke/requirements.txt
# Hidden credential prompt, or set MODEL_API_KEY as described below.
.\.venv\Scripts\python.exe scripts/smoke/validate_meta_models.py --live
```

This sends the existing repository produce image to Meta. Replace it with
`--image "C:\path\to\photo.jpg" --object "tomato"` for another image. Run one
check with `--checks vision`, `--checks sam` or `--checks planner`. The full check
normally makes five requests: text, vision, SAM and two Wonder tool turns.
Retries are disabled. A planner may take a third turn before the hard loop limit.

Results go to ignored `tmp/meta_validation/<run-id>/summary.json`; the SAM overlay
and full-image object masks are under that run's `sam/` directory. The suite fails
on incomplete responses, malformed vision data, parser diagnostics or no masks.
Visually inspect the overlay: these checks do not establish segmentation accuracy.
The planner history is an explicitly labeled fixture. The report is in
[docs/model_validation.md](../../docs/model_validation.md).

Offline tests (no key/network):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_meta_integration.py -q
```

The simpler individual access-check commands below remain available.

From the repository root, install the standalone dependency:

```powershell
python -m pip install -r scripts/smoke/requirements.txt
```

Set the full key privately in the current PowerShell session (input is hidden):

```powershell
$env:MODEL_API_KEY = [System.Net.NetworkCredential]::new("", (Read-Host "Meta API key" -AsSecureString)).Password
```

Alternatively, omit that step: each script invocation asks for the key using a
hidden prompt. Use the full key, not the masked/truncated dashboard display.
The script does not read `.env` or save your key. Clear the environment value when
finished with `Remove-Item Env:MODEL_API_KEY`.

```powershell
# 1. Text access check
python scripts/smoke/meta_models.py muse

# 2. Image understanding (choose your own real photo)
python scripts/smoke/meta_models.py vision --image "C:\path\to\tomatoes.jpg"

# 3. Image segmentation, with the same photo
python scripts/smoke/meta_models.py sam --image "C:\path\to\tomatoes.jpg" --object "tomato"

# 4. Optional planning-model access check
python scripts/smoke/meta_models.py wonder
```

Each invocation makes one real hosted request using the same team key and credits.
Images are uploaded to Meta. No automatic retries. An SDK timeout bounds network
operations; it is not a guaranteed hard wall-clock deadline for a live stream.
Responses, text and available usage are saved to ignored `tmp/meta_smoke/<run-id>/`.
Nothing runs on module import, and no AWS services or notifications are invoked.

## Interpret the result

- Muse text: a completed response with the requested access-check sentence.
- Muse vision: observations grounded in the image, with visibility limitations.
  This checks image input, not freshness accuracy.
- SAM: a completed stream and encoded output saved in `output.txt`. It is not
  ordinary prose/JSON. Completion does **not** prove useful segmentation: decode
  masks with the documented SAM parser and visually compare them with the photo.
  The SAM Playground is the easiest initial visual check. An empty match is a
  valid possibility; choose a clearly visible object and a short noun phrase.
- Wonder: a short proposed plan. This tests model access, not the future agent
  tool loop or real sensor control.

HTTP errors save the provider error body in `error.json`, without auth headers.
401 suggests a key problem; 402/403 can involve billing or access; 429 requires
checking the error details for rate limits versus exhausted quota. Check the Meta
Usage/Billing dashboard to confirm the requests use the intended team's credits.

Official references (checked 1 November 2026):

- [API quickstart](https://dev.meta.ai/docs/quickstart)
- [SAM requests](https://dev.meta.ai/docs/media-segmentation)
- [SAM parser and overlay libraries](https://dev.meta.ai/docs/sam/client-libraries)

The basic access checks use actual models. The complete adapter suite uses real
models with explicitly synthetic planner history; no fixture pretends to be a
provider response. Product UI, database and hardware integration remain separate work.

See [repository architecture](../../docs/repository_architecture.md) for the complete layout and implementation boundaries.
