# Tomato video: four-model recorded flow

Date: 1 November 2026. Application branch: `codex/meta-model-validation`.

The completed validation work and media are now included in `main`. The branch
above identifies where the model/demo implementation was developed.

For a login-free result, use the [narrated walkthrough](media/README.md) or run the
[self-contained local lab](../demos/video-model-flow/README.md). Its original and
overlay videos, audio and checkpoints are tracked in the application repository.

**Open the demo:** https://tomato-model-flow-lab.majormarch1.chatgpt.site

The Site is private; sign in with the ChatGPT account that owns this workspace.
Deployment was confirmed successful by Sites. The browser session used for QA was
not signed in to the private hosted Site, so its published page stopped at the
normal login gate. The identical static source was tested through local preview.
The Site deployment uses its own source repository; it does not deploy from the
application repository's `main` branch.

## What changed from the first validation

The earlier validation used a still produce photo and a synthetic batch-history
fixture. This run uses the user-selected real video, with actual video requests
to both SAM and Spark. Wonder receives the saved video observations through the
history tool, rather than the earlier synthetic history. No vendor is represented
as having performed a real action.

## Models actually executed

| Model | Actual input and result | Observed API latency |
| --- | --- | --- |
| `sam-3.1` | MP4 analysis copy, prompt `tomato`; 110 video frames processed, masks decoded for all 110 frames, overlay movie rendered | 5.54 s |
| `muse-spark-1.3` | Full uploaded video; structured output with 8 requested playback checkpoints and explicit limits | 24.64 s |
| `muse-wonder-1.0` | Real tool loop returning the recorded video history; proposed follow-up and missing-evidence requests | 21.01 s, including tool turns |
| `muse-voice-transcribe-1.0` | Separate 11.12-second synthetic spoken demo request; successful real transcription | 4.41 s |

These are one-run observations, not latency benchmarks. Local mask decoding and
overlay rendering take additional time and are excluded from API latency.

The original video is silent. Windows SAPI synthesized a demonstration request;
the Voice model transcribed that file. The source video was not represented as
having speech. Muse Image is not required by the chosen evidence workflow and was
not called. SAM, Spark, Wonder and Voice are the four planned runtime models.

## What the models returned

Spark categorized the requested playback checkpoints as follows:

| Playback seconds | Visual category | Proposed heuristic points |
| --- | --- | --- |
| 0, 4 | Mild visible concern | 35 |
| 8, 12, 16, 20 | Clear visible concern | 70 |
| 24, 27 | Severe visible concern | 100 |

The point mapping is application code, not a validated spoilage probability.
Spark described expansion of gray textured coverage near the stem and later
surface depression/wrinkling. The overlay identifies the tomato, not the type of
microorganism or a food-safety boundary. There is no hand-annotated mask benchmark.

Wonder compared the earlier and later observations, noted the absence of sensor
data and a characterized protocol, and requested further observation/alternate
views plus protocol characterization before scheduling a sensor measurement.
No exact expiry, actual elapsed storage time or disposition authorization was made.

Spark received the full clip. Its requested chronological descriptions are useful
for demonstration, but are **not** an independent prospective early-warning test:
future-frame leakage has not been experimentally excluded. The Wonder plan is
explicitly a full-clip summary, not a plan computed at each earlier checkpoint.

## What you can do in the link

1. Select **Walk through the pipeline** to inspect each of the six steps.
2. Listen to the synthetic request and read the real transcript.
3. Switch between **Original** and **SAM masks** video.
4. Select any checkpoint to see its actual saved Spark observation.
5. Inspect camera-only priority, absent sensor evidence and unavailable fused score.
6. Read Wonder's real tool-based plan and review the next recorded observation.
7. Open **Batch memory**, create a demo follow-up task and mark it reviewed locally.
8. Download an evidence receipt or inspect model response IDs and usage.

The webpage replays recorded inference; clicking buttons does not create new API
calls. Tasks and review confirmations are browser-local demonstrations. A physical
repeat measurement or Investigator A/B group experiment cannot be performed on a
single-sample time-lapse. No sensor reading or vendor outcome was fabricated.

## Source, processing and license

Source: [Pourrissement tomate](https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm),
by Lionel Allorge, Wikimedia Commons. Selected license:
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

The source was resized to 640 pixels wide, resampled to 4 fps and converted to
browser/API-compatible H.264 MP4. The resulting copy contains 110 frames / 27.5
playback seconds. Frames and model segmentation overlays were extracted; these
derived media are distributed under the same license. Attribution and links are
visible in the Site. The time-lapse does not supply the real-world capture interval.

## Reproduction and evidence

- [Buildless demo source and rerun instructions](../demos/video-model-flow/README.md)
- [Recorded results, model IDs and usage](validation/video_model_run.json)
- [Preview screenshot](assets/video_model_flow_preview.png)
- `scripts/smoke/prepare_video_demo.py`: source download, video conversion, optional synthetic speech.
- `scripts/smoke/video_flow_demo.py`: explicit live four-model execution and mask rendering.
- `scripts/smoke/export_video_demo.py`: assemble replay site from recorded artifacts.
- `scripts/smoke/preview_video_site.py`: localhost static server with byte-range support.

Local browser checks covered late-frame selection/seeking, SAM overlay switching,
voice walkthrough, Wonder-plan display, history navigation and demo task creation.
JavaScript syntax and Python compilation checks passed. The model-output bundle
was checked for eight checkpoints, all 110 decoded mask frames and null sensor /
fused values. No API key is present in the Site source or published data.

## Publication record

Site project: `appgprj_6ae74c5ae37481919e90a7d4c5a66c92`.
Source commit: `1ba1bd4e0a6fc2fd03ff1c6d0767543bd9f90e73`.
Deployment: `appgdep_6ae74f8a09e48191b0473a12c908951e` (succeeded).
The Site has a separate source repository; its own source branch is unrelated to
the application's protected `main` branch.
