# Setup and operations

This guide is the current startup reference for the repository. Run commands from the repository root unless a step says otherwise. Keep each server in its own terminal; stop it with **Ctrl+C**.

## 1. Requirements

- Python 3.12 or 3.13 with pip and venv.
- Node.js 22.17 or later with npm.
- Git and a Meta API key with access to the models you intend to run.
- Optional: an ESP32-S3 with SGP41 and BME280 sensors and an AWS account for cloud telemetry.

The visual workspace and model replay do not require AWS or connected hardware. The replay does not require a Meta key.

```sh
git clone https://github.com/saikoushikpallapolu/meta_2026.git
cd meta_2026
```

## 2. Install

### Windows PowerShell

No activation or execution-policy change is required:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev,models]"
if (!(Test-Path .env)) { Copy-Item .env.example .env }
npm --prefix frontend ci
```

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,models]'
test -f .env || cp .env.example .env
npm --prefix frontend ci
```

In the commands below, replace `.venv\Scripts\python.exe` with `.venv/bin/python` on macOS/Linux.

## 3. Configure `.env`

Edit `.env` locally and set:

```dotenv
MODEL_API_KEY=PASTE_YOUR_FULL_META_KEY_HERE
```

Use the complete key. The launcher reads `.env` from the repository root; existing shell variables take precedence. Restart the API after changing a key. Use `--ask-key` to enter a key at a hidden terminal prompt instead of storing it. That prompt overrides the key for that process.

| Variable | Default / purpose |
| --- | --- |
| `MODEL_API_KEY` | Server-only credential for SAM/Spark and Meta validation tools |
| `PRODUCT_DATABASE_URL` | `sqlite:///product_local.db`; visual workspace database |
| `PRODUCT_MEDIA_ROOT` | `data/media/uploads`; photos, analysis images, masks and crops |
| `DATABASE_URL` | Sensor database URL; blank selects complete RDS configuration or `sqlite:///backend_local.db` |
| `APP_ENVIRONMENT`, `APP_LOG_LEVEL` | Application environment/logging settings |
| `APP_CORS_ORIGINS` | Sensor API browser origin allowlist; local port 5173 by default |
| `VITE_API_BASE` | Public visual API base override; leave blank for the local `/api` proxy |
| `VITE_DEVICE_API_BASE` | Public sensor API base override; leave blank for the local sensor proxy |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Optional AWS IAM credentials; standard SDK role/session credentials also work |
| `AWS_SESSION_TOKEN` | Optional token for temporary AWS credentials |
| `AWS_REGION`, `AWS_DEFAULT_REGION` | `ap-south-1` |
| `AWS_IOT_ENDPOINT`, `AWS_IOT_TOPIC`, `AWS_IOT_CLIENT_ID` | IoT account endpoint, publish topic and node identity |
| `AWS_SQS_QUEUE_URL` | Worker input queue |
| `AWS_SNS_TOPIC_ARN` | Email/SMS alert topic |
| `AWS_S3_BUCKET` | Raw telemetry archive and deployment bundle bucket |
| `AWS_ADMIN_CIDR`, `AWS_RDS_ALLOWED_CIDR` | Required trusted ingress networks for opt-in cloud provisioning |
| `AWS_EC2_INSTANCE_ID` | Target for opt-in cloud diagnostics |
| `AWS_RDS_IDENTIFIER` | Database instance identifier used by provisioning scripts |
| `AWS_RDS_ENDPOINT`, `AWS_RDS_PORT` | PostgreSQL host and port, default `5432` |
| `AWS_RDS_USER`, `AWS_RDS_PASSWORD`, `AWS_RDS_DBNAME` | Database credentials/name |

Only `VITE_*` variables are intended for browser configuration. Keep Meta and AWS keys out of them. Vite reads root `.env` at startup; restart it after public URL changes. The app uses environment credentials rather than browser key-entry forms.

For sensor PostgreSQL, use either `DATABASE_URL` or both RDS endpoint and password. Partial RDS configuration raises an error. A configured database connection failure is reported rather than silently redirecting writes to another database.

## 4. Build 2: visual inspection workspace

**Terminal 1:**

```powershell
.venv\Scripts\python.exe scripts/run_product.py
```

**Terminal 2:**

```powershell
cd frontend
npm run dev
```

| Interface | URL |
| --- | --- |
| Visual workspace | http://127.0.0.1:5173/ |
| API health | http://127.0.0.1:8080/health |
| Model capability status | http://127.0.0.1:8080/api/capabilities |
| Interactive API docs | http://127.0.0.1:8080/docs |

1. Register a batch with a name and quantity. Choose a whole number for tomato counts or a decimal for kilograms.
2. Choose a JPEG/PNG, save it, or import one of the attributed public samples.
3. Open its inspection and choose **Analyse tomatoes**. New analysis sends the image to Meta and may consume credits.
4. Explore the segmentation overlay and per-item evidence. Filters and saved results do not make new model calls.
5. Confirm or correct findings with a human review. Reviews are saved separately from model output.

Uploads are limited to 10 MiB and 20 megapixels. Photo analysis processes up to 32 candidate regions; crop a crowded scene or use a smaller group if needed. Without a key, registration, capture, imports and saved history remain available; new analysis is disabled. A key being loaded confirms configuration, not account permission or provider availability.

The API stores jobs durably. Queued jobs can run at startup when a key is configured. Failed or interrupted attempts require an explicit retry in the interface, avoiding automatic repeated model charges.

## 5. Build 1: sensor dashboard

Keep the frontend running. In another terminal:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[cloud]"
.venv\Scripts\python.exe scripts/run_product.py --mode sensor
```

| Interface | URL |
| --- | --- |
| Sensor dashboard | http://127.0.0.1:5173/?view=device |
| Sensor health | http://127.0.0.1:8081/health |
| Known devices | http://127.0.0.1:8081/devices |
| Sensor API docs | http://127.0.0.1:8081/docs |

Device IDs come from submitted telemetry. The dashboard shows a waiting state until readings are available and refreshes every four seconds. A device is offline when its last received packet is older than 15 seconds. Select a device to see its readings and history. Previously recorded readings remain visible when the node disconnects.

To check the local HTTP ingestion path without AWS, submit one explicitly identified development packet. This writes a local test reading and can trigger configured alerts; use a development database and leave SNS blank for this check:

```powershell
$packet = @{ device_id='Local-Test-Node'; food_type='tomato'; temperature_c=25; humidity_pct=60; voc_raw=31800; nox_raw=16800 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8081/telemetry -ContentType application/json -Body $packet
```

### Hardware and AWS telemetry

The firmware uses **SGP41** for VOC/NOx and **BME280** for temperature, humidity and pressure, connected over I²C to an ESP32-S3. Wiring, libraries, and certificate setup are in [Sensor/README.md](../Sensor/README.md). Copy `Sensor/secrets.example.h` to `Sensor/secrets.h` and fill in the Wi-Fi credentials, AWS endpoint, device identity, topic, and certificates. Both `.env` and `secrets.h` are ignored by Git.

Configure AWS IoT Core to route `telemetry/device/+/telemetry` to SQS and the S3 archive. Set the queue URL and database settings in `.env`, then run a separate worker:

```powershell
.venv\Scripts\python.exe scripts/run_product.py --mode worker
```

The worker persists raw readings, complete inference snapshots, and state-transition events to the sensor database. The API and worker must point to the **same database**. New sessions establish their own gas baseline. Temperature profiles are stored in `config/food_types/`. Processing baselines and cumulative thermal state currently live in worker memory; restarting the worker starts a new session while retaining prior records.

The sensor API and visual API use separate local databases by default. Photo batches are not automatically linked to sensor sessions. Keep each API at one local process for this setup; coordinate database migration ownership before scaling.

### Alerts

- **Browser:** grant notification permission from the sensor dashboard; the page must remain open.
- **Email/SMS:** set `AWS_SNS_TOPIC_ARN` and AWS credentials/role permissions, then subscribe through the dashboard. Complete any SNS confirmation and account-specific SMS setup.
- The worker sends alerts at its configured risk threshold or detected onset, with a per-device cooldown. The direct `/telemetry` path also runs inference.

Cloud deployment scripts under `scripts/deploy_aws_*.py` provision real billable resources. Review the IAM, network, database and hosting configuration before running them. They are separate from local startup and are not invoked by these commands. HTTPS hosting also needs HTTPS API URLs and appropriate access controls.

## 6. Model testing lab

From another terminal:

```powershell
.venv\Scripts\python.exe scripts/smoke/preview_video_site.py --directory demos/video-model-flow
```

Open **http://127.0.0.1:8767/**. This dashboard replays saved outputs from the four-model video experiment. It supports seeking through the video, exploring batch history, and viewing model receipts. Opening it does not make new model requests. Sources and media licenses are included in the [lab guide](../demos/video-model-flow/README.md).

To request a new provider validation run, follow [model validation](model_validation.md) and [smoke-check instructions](../scripts/smoke/README.md); those are explicit, potentially billable commands.

## 7. Verification

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp=tmp/verification
npm --prefix frontend run build
npm --prefix frontend run lint
```

Use a disposable pytest directory. Tests isolate their databases and media and do not call AWS or Meta. The development extra includes the sensor SDK needed by offline API tests. To inspect startup without a model call, request `/health` and `/api/capabilities`.

`npm --prefix frontend run build` generates `frontend/dist`. A build alone does not start servers. The sensor API can serve the built frontend at its own origin when this directory exists; the default development flow uses Vite to connect the two APIs. When hosting a combined build, configure `VITE_API_BASE` to reach the standalone visual API if live photo analysis is needed.

## 8. Troubleshooting

| Symptom | Check |
| --- | --- |
| Port 5173 is in use | Stop the existing Vite process; strict-port startup avoids silently moving the dashboard. |
| Workspace cannot reach API | Run the product API on 8080. Restart Vite after proxy changes. |
| Sensor feed unavailable | Start `--mode sensor` on 8081. The product API alone does not expose telemetry. |
| No devices listed | Connect hardware, run the AWS worker, or submit a development packet. Devices appear after ingestion. |
| Live analysis disabled | Set `MODEL_API_KEY` in root `.env` and restart the product API. Check for a shell variable overriding it. |
| Model authentication/access error | Check the full key, model permissions, credits and provider status; use explicit retry after fixing the cause. |
| Image rejected | Use a still JPEG/PNG within the size limits; keep tomatoes visible and avoid overly crowded scenes. |
| Missing history after restart | Check database/media paths and working directory. Back up and restore the database and media root together. |
| RDS configuration error | Set both endpoint and password, or clear both for local SQLite. Do not point tests at production storage. |
| Email/SMS not received | Check SNS topic, IAM permissions, confirmation status, SMS account settings and cooldown. |

Use `--port` to change either API's listening port. If you change a local API port, update the matching proxy target in `frontend/vite.config.js` and restart Vite. Use `--port` on the replay server to change port 8767.

## Supporting tools

Dataset stitching, PDF generation, and video preparation use optional libraries. Install `python -m pip install -e ".[tools]"` before running those scripts. The full runtime compatibility file, `requirements.txt`, installs the application with the `cloud` and `models` extras from the repository root.
