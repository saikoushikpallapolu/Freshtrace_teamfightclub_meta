# Verification

Run `python -m pytest tests -q --basetemp=tmp/verification` with `.[dev,models]` installed. Use a disposable base directory. Tests use temporary SQLite databases, local media, and controlled provider responses; no AWS or Meta calls are made.

- `unit/`: Meta request/response contracts, mask picking, crop alignment, planning bounds, and sensor calibration/timing/sequence checks.
- `integration/`: batch/media persistence, migrations, job/review lifecycle, retries, concurrent claims, sample provenance, and sensor API snapshots/device isolation.
- `e2e/`: reserved for automated browser journeys. Browser/physical/provider checks remain explicit operations.

For all startup commands and ports, see [setup](../docs/setup.md). For audit scope and results, see [repository audit](../docs/repository_audit.md).
