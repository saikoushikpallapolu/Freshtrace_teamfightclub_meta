# Walkthrough videos and lab captures

These are intentionally versioned deliverables, unlike ignored scratch files in
`tmp/` and draft exports in `output/`. Replay needs no API key or hosted-site login.

- [Narrated walkthrough MP4](model_lab_walkthrough.mp4): 3 minutes 36 seconds,
  H.264/AAC, 1600 x 900, approximately 5.9 MB. Edited lab captures, real original/SAM
  clips, local synthetic narration and burned-in captions.
- [Subtitle file](model_lab_walkthrough.srt): optional separate captions.
- [Chapter timestamps](model_lab_walkthrough_chapters.txt).
- [Narration transcript and source attribution](model_lab_walkthrough_transcript.md).
- `lab-captures/`: eight full-page lab screenshots and their JSON crop bounds,
  used by the video builder. These are images of the demonstration lab, not
  unrelated desktop windows or vendor records.

The original tomato video, analysis/overlay movies, request audio and checkpoint
stills are in [the standalone lab](../../demos/video-model-flow/README.md).

## Rebuild the narration video

On Windows with Python 3.12, Segoe UI fonts and Windows SAPI available:

```powershell
python -m pip install -r scripts/smoke/video_requirements.txt
python scripts/smoke/build_lab_walkthrough.py
```

The builder reads checked-in screenshots, crop bounds and replay clips. It writes
draft output to ignored `output/video/` and intermediates to ignored
`tmp/walkthrough/`. It makes no API calls and does not access credentials.
Review rebuilt output before replacing the approved deliverables here.

## Provenance and license

Source video: [Pourrissement tomate](https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm)
by Lionel Allorge, Wikimedia Commons, under
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
Changes: resizing, sampling, model overlays, edited lab captures and explanatory
narration. Derived video/media is distributed under the same license. No creator
endorsement is implied. Narration is locally synthesized; the source clip is silent.

The video explains a recorded model run. It does not claim live sensor readings,
physical investigations, actual vendor actions or validated food-safety results.
