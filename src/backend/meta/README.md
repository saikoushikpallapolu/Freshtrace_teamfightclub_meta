# Hosted Meta integrations

- `client.py`: explicit server-only credentials, Meta endpoint/model identifiers, normalized image inputs and bounded request timeouts.
- `segmentation.py`: strict SAM result parsing and decoded masks/overlays.
- `inspection.py`: SAM followed by contextual Spark item inspection, aligned crops and exact-mask hit maps.
- `vision.py`: structured scene-level visual observations.
- `planner.py`: bounded, read-only Wonder history-tool loop.

These adapters do not make requests on import. The product worker calls the photo inspection pipeline only for queued jobs. Voice and four-model video checks are explicit scripts under `scripts/smoke/`; saved results are presented in the local model lab.

Install `python -m pip install -e ".[models]"`. See [setup](../../../docs/setup.md), [model validation](../../../docs/model_validation.md), and [architecture](../../../docs/repository_architecture.md).
