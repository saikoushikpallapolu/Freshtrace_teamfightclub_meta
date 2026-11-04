# Media and artifact storage

`media.py` validates still JPEG/PNG uploads, bounds size/pixels, preserves original bytes by content hash, and creates normalized oriented JPEGs. Immutable file publication is atomic. The perception worker writes per-attempt masks, crops, overlays and hit maps under the configured media root; API retrieval is batch-scoped.

Back up the media root and database together. Local uploads and model artifacts are excluded from Git. See [setup](../../../docs/setup.md).
