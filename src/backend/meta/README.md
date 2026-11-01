# Hosted Meta adapters

Implemented and live-tested on 1 November 2026:

- `client.py`: server-only Meta client and orientation-normalized image input.
- `segmentation.py`: strict SAM parsing, decoded per-object masks and overlays.
- `vision.py`: Spark observations validated against a strict Pydantic JSON schema.
- `planner.py`: bounded Wonder history-tool round trip; one read-only tool only.

No AWS or inference starts on import. The caller supplies credentials and history.
Product API endpoints, sensor orchestration, persistent task state and optional
transcription remain future work. The test fixture is explicitly synthetic; it is
not a real vendor database or a real device operation.

Use Python 3.12 for the validated environment. Install with
`python -m pip install -r scripts/smoke/requirements.txt` or the package's `models`
extra. See [validation report](../../../docs/model_validation.md) for results and
known limitations. No model weights need to be downloaded for these hosted APIs.

See [repository architecture](../../../docs/repository_architecture.md) for the complete layout and implementation boundaries.
