# Product API endpoints

- `batches.py`: batch registration/history, bounded photo upload and batch-scoped media access.
- `inspection.py`: capabilities, durable job start/retry/status, artifact access and append-only reviews.
- `samples.py`: attributed local sample listing, checksum validation and repeat-safe import.

The standalone product API registers these routers before startup. The sensor API also exposes storage routes for combined deployments; its embedded photo-analysis worker is disabled. Use the standalone product API for live visual inspection. See [setup](../../../../docs/setup.md).
