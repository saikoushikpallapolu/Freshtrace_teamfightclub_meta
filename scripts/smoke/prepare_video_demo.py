"""Download the selected Commons clip and prepare a small, silent MP4 analysis copy."""

import argparse
import os
import subprocess
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, default=Path("tmp/video_demo"))
    parser.add_argument(
        "--synthesize-voice",
        action="store_true",
        help="Windows only: create a clearly synthetic spoken demonstration request.",
    )
    args = parser.parse_args()
    import imageio_ffmpeg

    directory = args.workdir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "source.webm"
    if not source.exists():
        request = urllib.request.Request(
            "https://upload.wikimedia.org/wikipedia/commons/a/a6/Pourrissement_tomate.webm",
            headers={"User-Agent": "ProduceModelDemo/1.0 (educational video analysis)"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            source.write_bytes(response.read())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-vf",
            "scale=640:-2,fps=4",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(directory / "sample.mp4"),
        ],
        check=True,
        capture_output=True,
    )
    if args.synthesize_voice:
        if os.name != "nt":
            raise ValueError(
                "Windows SAPI synthesis is unavailable. Supply your own demo_request.wav instead."
            )
        environment = os.environ.copy()
        environment["DEMO_AUDIO_PATH"] = str(directory / "demo_request.wav")
        script = """
$voice = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Format.Type = 22
$stream.Open($env:DEMO_AUDIO_PATH, 3, $false)
$voice.AudioOutputStream = $stream
$null = $voice.Speak('Check this tomato batch. Compare the earlier and later observations. Tell me what to inspect next, and ask for a sensor measurement if evidence is missing.')
$stream.Close()
"""
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env=environment,
            check=True,
            capture_output=True,
        )
    wav = directory / "demo_request.wav"
    if wav.exists():
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(wav),
                "-ac",
                "1",
                "-ar",
                "24000",
                "-c:a",
                "pcm_s16le",
                str(directory / "voice_request.wav"),
            ],
            check=True,
            capture_output=True,
        )
    print(f"Prepared {directory}. Source: Lionel Allorge / CC BY-SA 3.0. Original video is silent.")


if __name__ == "__main__":
    main()
