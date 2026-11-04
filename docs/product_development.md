# Product development

Use the [setup guide](setup.md) for current commands, configuration, and all dashboard ports. The [visual inspection guide](visual_prototype.md) describes item evidence and review behavior.

The product API owns batches, photo assets, observations, persistent perception jobs, model receipts, and append-only human reviews. A saved photo can be reopened by batch and observation URL. Media retrieval is scoped to its batch, and mutation receipts support retry-safe batch creation, media upload, and observation creation.

Database startup applies ordered Alembic migrations while preserving existing sensor tables. Local originals are stored alongside normalized display images and derived analysis artifacts. Back up the database and media root together.

Development checks use disposable SQLite databases and controlled model responses. The local launcher binds to loopback; public deployment needs authentication, ownership checks, and a migration/deployment strategy. Refer to the [repository audit](repository_audit.md) for verified scope and the [architecture](repository_architecture.md) for the source map.
