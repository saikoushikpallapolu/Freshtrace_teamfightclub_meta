# Product workflows

`perception.py` owns durable analysis enqueue/claim/complete/fail transitions, provider-call receipts, explicit retry boundaries, and worker leases. A claimed attempt runs the Meta inspection pipeline and publishes persisted evidence for the API/UI. The optional injected pipeline supports offline integration tests without a provider request.

Future investigation and stock-action workflows are tracked in the [implementation plan](../../../docs/phased_implementation_plan.md).
