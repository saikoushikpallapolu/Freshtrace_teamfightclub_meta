"""Run a real four-model, recorded video demo; no key is written to disk."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from getpass import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", required=True, action="store_true")
    parser.add_argument("--workdir", type=Path, default=ROOT / "tmp/video_demo")
    args = parser.parse_args()
    from backend.meta.client import make_client
    from backend.meta.planner import plan_with_history
    from backend.meta.segmentation import render_segmentation
    from meta_sam_parser import CompletedOutcome, video_segmentation_format
    from PIL import Image
    import httpx
    import imageio_ffmpeg

    key = os.environ.get("MODEL_API_KEY", "") or getpass("Full Meta key (hidden): ")
    work = args.workdir
    cache = work / "responses"
    cache.mkdir(exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    sample = work / "sample.mp4"
    checkpoints = [0, 4, 8, 12, 16, 20, 24, 27]

    def save(name, data):
        (cache / (name + ".json")).write_text(
            json.dumps(data, indent=2, ensure_ascii=False).replace(key, "[REDACTED]"), encoding="utf-8")

    with make_client(key) as client:
        if (cache / "upload.json").exists():
            uploaded = json.loads((cache / "upload.json").read_text())
        else:
            with sample.open("rb") as f:
                uploaded = client.files.create(file=f, purpose="user_data").model_dump(mode="json")
            save("upload", uploaded)
        file_id = uploaded["id"]
        print("Video uploaded; starting recorded model calls.", flush=True)

        def record(name, function):
            path = cache / (name + ".json")
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            start = perf_counter()
            value = function()
            value["elapsed_seconds"] = round(perf_counter() - start, 2)
            save(name, value)
            print(name + " completed", flush=True)
            return value

        def voice_call():
            with (work / "voice_request.wav").open("rb") as f:
                r = httpx.post(
                    "https://api.meta.ai/v1/asr/transcribe", params={"sessionId": "tomato-video-demo"},
                    headers={"Authorization": "Bearer " + key},
                    files={"request": (None, json.dumps({"model": "muse-voice-transcribe-1.0",
                                                          "mode": "DIARIZATION", "audioEncoding": "WAV"}), "application/json"),
                           "audio": ("voice_request.wav", f, "audio/wav")}, timeout=120,
                )
            if r.status_code >= 400:
                save("voice_error", {"status": r.status_code, "body": r.json()})
                raise ValueError(f"Voice API HTTP {r.status_code}; see saved redacted error.")
            return {"model": "muse-voice-transcribe-1.0", "input_kind": "synthetic Windows SAPI demonstration request; not video audio",
                    "response": r.json()}

        def spark_call():
            schema = {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "summary": {"type": "string"},
                    "checkpoints": {"type": "array", "items": {
                        "type": "object", "additionalProperties": False,
                        "properties": {"second": {"type": "number"}, "observation": {"type": "string"},
                                       "visible_concern": {"type": "string", "enum": ["none_observed", "mild", "clear", "severe"]},
                                       "next_check": {"type": "string"}},
                        "required": ["second", "observation", "visible_concern", "next_check"]}},
                    "limits": {"type": "array", "items": {"type": "string"}}},
                "required": ["summary", "checkpoints", "limits"],
            }
            prompt = (
                "Analyze this accelerated time-lapse as visual evidence for an inspection assistant. "
                "Do not assume the real-world elapsed hours or biological identity from playback time. "
                "No sensor data, smell, safety or expiry measurements are supplied. "
                f"Return exactly one chronological checkpoint at each requested playback second: {checkpoints}. "
                "Describe what is visible at that point without later evidence leaking into earlier observations. "
                "visible_concern is only an ordinal visual-inspection category, not a probability. "
                "Name the next useful check and visibility limitations."
            )
            r = client.responses.create(
                model="muse-spark-1.3", input=[{"role": "user", "content": [
                    {"type": "input_text", "text": prompt}, {"type": "input_file", "file_id": file_id}]}],
                text={"format": {"type": "json_schema", "name": "video_observations", "strict": True, "schema": schema}},
                max_output_tokens=8192,
            )
            if r.status != "completed":
                raise ValueError("Spark video response incomplete")
            parsed = json.loads(r.output_text)
            if [x["second"] for x in parsed["checkpoints"]] != checkpoints:
                raise ValueError("Spark checkpoint times do not match the requested timeline")
            return {"response": r.model_dump(mode="json"), "observation": parsed}

        def sam_call():
            with client.responses.stream(
                model="sam-3.1", input=[{"role": "user", "content": [
                    {"type": "input_text", "text": "tomato"},
                    {"type": "input_video", "file_id": file_id}]}], metadata={"mask_encoding": "one_bit"},
            ) as stream:
                for _ in stream:
                    pass
                r = stream.get_final_response()
            if r.status != "completed":
                raise ValueError("SAM video response incomplete")
            return {"response": r.model_dump(mode="json")}

        with ThreadPoolExecutor(max_workers=3) as pool:
            voice_f = pool.submit(record, "voice", voice_call)
            spark_f = pool.submit(record, "spark", spark_call)
            sam_f = pool.submit(record, "sam", sam_call)
            voice, spark, sam = voice_f.result(), spark_f.result(), sam_f.result()

        # Decode every returned video frame rather than treating output text as a result.
        parser = video_segmentation_format().create_parser()
        text = "".join(part.get("text", "") for item in sam["response"]["output"]
                       for part in item.get("content", []) if part.get("type") == "output_text")
        parser.push(text)
        parsed = parser.finish(CompletedOutcome()).result
        if parsed.diagnostics:
            raise ValueError("SAM video has parser diagnostics")
        frames = work / "frames"
        frames.mkdir(exist_ok=True)
        subprocess.run([ff, "-y", "-i", str(sample), "-q:v", "3", str(frames / "frame_%04d.jpg")], check=True, capture_output=True)
        grouped = {}
        for item in parsed.records:
            if item.kind == "mask" and item.frame:
                grouped.setdefault(item.frame.frame_index, []).append(item)
        stats = []
        frame_files = sorted(frames.glob("frame_*.jpg"))
        for i, path in enumerate(frame_files):
            with Image.open(path) as image:
                report = render_segmentation(SimpleNamespace(records=grouped.get(i, []), diagnostics=[]),
                                             image, work / "overlays" / f"frame_{i:04d}")
            stats.append({"frame": i, "playback_second": i / 4, "mask_count": report["mask_count"],
                          "area_pixels": sum(x["foreground_pixels"] for x in report["objects"])})
        # Emit a normal browser-playable overlay video.
        from shutil import copyfile
        render_frames = work / "render_frames"
        render_frames.mkdir(exist_ok=True)
        for i in range(len(frame_files)):
            copyfile(work / "overlays" / f"frame_{i:04d}" / "sam_overlay.jpg", render_frames / f"frame_{i:04d}.jpg")
        subprocess.run([ff, "-y", "-framerate", "4", "-i", str(render_frames / "frame_%04d.jpg"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(work / "overlay.mp4")], check=True, capture_output=True)

        observations = spark["observation"]["checkpoints"]
        for checkpoint in observations:
            i = min(round(checkpoint["second"] * 4), len(frame_files) - 1)
            checkpoint["frame_index"] = i
            checkpoint["mask_count"] = stats[i]["mask_count"]
            checkpoint["sensor_status"] = "not_measured"
            checkpoint["combined_score"] = None
            checkpoint["visual_priority_points"] = {"none_observed": 0, "mild": 35, "clear": 70, "severe": 100}[checkpoint["visible_concern"]]

        history = {"data_source": "real_model_observations_from_public_timelapse_demo_not_vendor_trial",
                   "batch_id": "VIDEO-TOMATO-01", "voice_request": voice["response"].get("transcript", ""),
                   "observations": observations, "sensor_session": None,
                   "sensor_protocol": {"characterized": False}, "physical_group_tests": "unavailable_in_video",
                   "elapsed_storage_time": "unknown; playback seconds are not hours/days",
                   "stock_disposition_authorized": False}

        def wonder_call():
            responses, trace = plan_with_history(client, history["batch_id"], history)
            return {"responses": [r.model_dump(mode="json") for r in responses],
                    "tool_trace": trace, "plan": responses[-1].output_text}

        wonder = record("wonder", wonder_call)
        bundle = {"run_utc": datetime.now(timezone.utc).isoformat(),
                  "source": {"title": "Pourrissement tomate", "author": "Lionel Allorge",
                             "page": "https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm",
                             "original_url": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Pourrissement_tomate.webm",
                             "license": "CC BY-SA 3.0", "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
                             "changes": "Resized to 640px, resampled to 4 fps; extracted frames; model mask overlays added.",
                             "sha256": hashlib.sha256((work / "source.webm").read_bytes()).hexdigest()},
                  "fps": 4, "frame_count": len(frame_files), "duration_seconds": len(frame_files) / 4,
                  "mode": "recorded_real_model_run_with_browser_local_workflow_demo",
                  "voice": voice, "spark": {"observation": spark["observation"], "elapsed_seconds": spark["elapsed_seconds"],
                                             "response_id": spark["response"]["id"], "usage": spark["response"].get("usage")},
                  "sam": {"response_id": sam["response"]["id"], "elapsed_seconds": sam["elapsed_seconds"],
                          "usage": sam["response"].get("usage"), "frames": stats,
                          "frames_with_masks": len(grouped), "diagnostics": []},
                  "wonder": {"plan": wonder["plan"], "tool_trace": wonder["tool_trace"],
                             "elapsed_seconds": wonder["elapsed_seconds"],
                             "calls": [{"response_id": r["id"], "model": r["model"], "usage": r.get("usage")} for r in wonder["responses"]]}}
        (work / "demo_data.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False).replace(key, "[REDACTED]"), encoding="utf-8")
        print(f"Complete: {len(frame_files)} frames, {len(grouped)} SAM frames with masks; four models recorded.", flush=True)


if __name__ == "__main__":
    main()
