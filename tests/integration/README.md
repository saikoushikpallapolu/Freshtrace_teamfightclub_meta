# Integration tests

API and storage checks use disposable SQLite databases and media directories. They exercise batch scoping, migration preservation, idempotent writes, durable jobs, explicit retry, review persistence, public-sample provenance, and sensor snapshots/device separation. Provider behavior is injected for offline checks; cloud services are not contacted.

Run `python -m pytest tests/integration -q --basetemp=tmp/integration-check` with `.[dev,models]` installed.
