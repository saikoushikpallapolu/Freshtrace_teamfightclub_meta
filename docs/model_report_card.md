# Model report card

Update: a later real multi-item prototype run is documented in the
[visual prototype report](visual_prototype.md). It includes three completed inputs
and a full-scene capacity stop. Accuracy still lacks independent labels; the
single-tomato assessment below remains the earlier 1 November baseline.

Based on the recorded 1 November 2026 run. This is an integration assessment,
not a validated food-quality benchmark. Evidence: [recorded results](validation/video_model_run.json).

## Measured results

| Component | Measured result | Accuracy status |
| --- | --- | --- |
| SAM 3.1 | Masks on 110/110 video frames; zero parsing diagnostics; visually reviewed overlay | 100% frame coverage is not mask accuracy. Human-reference IoU/Dice is unmeasured. |
| Muse Spark | Eight requested checkpoints returned in structured output | Visual-category accuracy/F1 is unmeasured; no independent reference labels. |
| Muse Wonder | Completed one history-tool loop using two model calls | Followed constraints in this case; planning quality is not established across scenarios. |
| Voice Transcribe | Zero word edits across 26 reference words, after case/punctuation normalization | 0% WER on one 11.12-second synthetic request only. Real-speaker/noise performance is unmeasured. |

The offline boundary suite passed 13 tests. Those check code/schema behavior,
orientation, errors and tool restrictions; they do not measure model accuracy.

## Runtime and estimated expense

| Model | Observed API latency | Estimated USD |
| --- | --- | --- |
| SAM | 5.54 s | 0.022 |
| Spark | 24.64 s | 0.026 |
| Wonder, two turns | 21.01 s | 0.056 |
| Voice | 4.41 s | 0.00055 |

Total is approximately $0.105 for this run using recorded usage and published
standard rates, not an invoice. Upload, conversion and local decoding/rendering
add time. Single observations do not establish average or p95 latency.
[Pricing reference](https://dev.meta.ai/docs/pricing-rate-limits).

## Limits and observed concerns

- One stationary tomato on a plain background does not represent crowded crates.
- The first video frame already has visible dark spots and a fuzzy-looking patch;
  the model's initial "mild" category needs independent human review.
- Spark saw the full video. This does not prove prospective early warning or
  exclude later-frame information influencing earlier descriptions.
- No physical sensor fusion or A/B localization trial was performed.
- Voice input was clean synthetic speech, not vendor speech in background noise.
- An earlier unconstrained plan suggested procedures/timings without a characterized
  sensor protocol. Constrained tools improved the tested result; code must enforce limits.
- The first forced-tool-choice request failed with HTTP 400. Compatibility was
  fixed and the planner rerun passed; this is not proof of universal API reliability.

## Recommendation

Proceed with the application and an evaluation harness. Keep the base models for
now; collect independent labeled batches before deciding whether tuning is needed.

Use versioned protocol lookup or retrieval for approved operating guidance. Query
batch histories and sensor values through structured tools. Ordinary RAG supplies
retrieved context without retraining model weights; it cannot repair inconsistent
sensor measurements or automatically improve object masks.

Consider fine-tuning only after held-out evaluation identifies a repeatable task
weakness that prompting, examples, capture improvements and retrieval do not fix.
The hosted endpoints tested here do not themselves establish fine-tuning support.

## Next metrics

- SAM: mask IoU/Dice, missed objects, false detections and tracking failures.
- Spark: confusion matrix, macro-F1, serious-visible-concern recall, false alarms,
  unsupported statements and ambiguous-case handling.
- Wonder: valid tool calls, task completion, protocol violations and useful abstention.
- Voice: WER, intent accuracy and errors in batch IDs/quantities across real speakers.
- Product: correct/wrong/unresolved priorities, task time and comparison with
  image-only, sensor-only and FIFO baselines.

Split development/test data by physical batch, not neighboring photos or frames.
See the [physical testing roadmap](testing_roadmap.md) for the next experiments.
