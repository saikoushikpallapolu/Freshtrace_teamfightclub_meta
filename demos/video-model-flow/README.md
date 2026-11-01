# Recorded video model-flow demo

Private hosted demo: https://tomato-model-flow-lab.majormarch1.chatgpt.site

Sign in with the ChatGPT account that owns the Site. This is an interactive
replay of actual model outputs, not a production vendor app or a browser API-key
form. The product name remains undecided. The Site has its own source repository;
the parent application's `main` branch is not used for deployment.

`index.html`, `style.css` and `app.js` are the buildless presentation source.
Generated video, masks, raw responses and credentials are not stored in this folder.
The export script assembles an isolated static directory from the recorded run.

## Reproduce the analysis

Use Python 3.12. Run from the application repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r scripts/smoke/video_requirements.txt
.\.venv\Scripts\python.exe scripts/smoke/prepare_video_demo.py --synthesize-voice
.\.venv\Scripts\python.exe scripts/smoke/video_flow_demo.py --live
.\.venv\Scripts\python.exe scripts/smoke/export_video_demo.py
.\.venv\Scripts\python.exe scripts/smoke/preview_video_site.py --directory tmp/video-demo-site
```

The live script asks for the key with hidden input, or reads `MODEL_API_KEY` from
the process environment. It uploads the video and makes real billed calls. The
default work directory is ignored `tmp/video_demo/`. Successful model responses
are cached there for replay; use a new `--workdir` when changing the input/prompt
or when deliberately requesting a new run. Preparation supports a different work
directory too. On non-Windows hosts, provide `demo_request.wav` rather than using
SAPI speech synthesis, then rerun preparation to normalize it.

## Demonstrated flow

1. Real Voice Transcribe call on a separately synthesized demonstration request.
2. Real SAM video segmentation, parsed and rendered into an overlay movie.
3. Real Spark full-video analysis with eight structured checkpoints.
4. Camera-only code policy mapping categories to heuristic inspection points.
5. Real Wonder tool loop reading saved video history; no physical experiment.
6. Recorded history, local demo follow-up tasks and downloadable evidence receipt.

The video is silent. No VOC/NOx readings, sensor-driven score changes, real-time
storage durations or stock outcomes are fabricated. Muse Image is outside this
workflow and was not called. Voice is an optional product input but was included
to exercise all four planned runtime models.

## Media attribution

“Pourrissement tomate” by Lionel Allorge, Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm

Selected license: CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/ .
Changes: resized to 640 pixels, resampled to 4 fps, frames extracted and model
mask overlays added. Derived media is distributed under the same license.
No endorsement is implied. Attribution is also visible in the hosted demo.
