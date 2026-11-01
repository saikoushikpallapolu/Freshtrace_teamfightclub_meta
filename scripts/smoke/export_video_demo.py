"""Assemble the buildless replay site from recorded model results; no API calls."""

import argparse
import json
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, default=ROOT / "tmp/video_demo")
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/video-demo-site")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = json.loads((args.workdir / "demo_data.json").read_text(encoding="utf-8"))
    for name in ("index.html", "style.css", "app.js"):
        copyfile(ROOT / "demos/video-model-flow" / name, args.output / name)
    for name in ("sample.mp4", "overlay.mp4", "voice_request.wav", "demo_data.json"):
        copyfile(args.workdir / name, args.output / name)
    for j, checkpoint in enumerate(data["spark"]["observation"]["checkpoints"]):
        i = checkpoint["frame_index"]
        copyfile(args.workdir / "frames" / f"frame_{i + 1:04d}.jpg", args.output / f"checkpoint_{j}.jpg")
        copyfile(args.workdir / "overlays" / f"frame_{i:04d}" / "sam_overlay.jpg",
                 args.output / f"checkpoint_overlay_{j}.jpg")
    print(f"Exported recorded replay to {args.output}")


if __name__ == "__main__":
    main()
