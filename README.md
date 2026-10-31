# meta_2026

Produce inspection and stock-priority assistant combining batch history,
sensor evidence, guided investigations and human-confirmed stock actions.
The product name is undecided.

## Project documents

- [Product and build plan](docs/product_build_plan.pdf): unified product flow,
  model roles, scoring, implementation milestones and evaluation.
- [Repository architecture](docs/repository_architecture.md): current runtime,
  complete directory structure, planned files, ownership boundaries and known gaps.

The existing application is a React/Vite dashboard, FastAPI telemetry API,
Python inference worker and ESP32-S3 sensor firmware. New product folders are
documented scaffolding; they do not yet implement the Meta-powered workflows.
Existing runtime entry points and deployment scripts remain in place.
