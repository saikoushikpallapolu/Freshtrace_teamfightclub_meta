# Database migrations

Ordered Alembic upgrades run through `persistence/migrate.py` using an explicit database connection:

| Revision | Purpose |
| --- | --- |
| `0001_product_foundation` | Batches, media, observations, sensor-link schema and model-call receipts |
| `0002_request_receipts` | Durable mutation retry receipts |
| `0003_perception_jobs` | Analysis jobs, sample IDs and human reviews |
| `0004_sensor_snapshot` | Complete persisted sensor inference results |

The initializer preserves legacy sensor tables and applies forward upgrades. Back up the database and media together and use one migration owner at startup. Destructive downgrades are not part of the application flow. See [architecture](../../../../docs/repository_architecture.md).
