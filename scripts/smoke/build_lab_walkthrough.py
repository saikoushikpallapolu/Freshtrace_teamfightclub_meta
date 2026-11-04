"""Build an edited, narrated MP4 from captured lab screens and real model output."""

import json
import math
import os
import subprocess
import textwrap
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "tmp/walkthrough"
OUT = ROOT / "output/video"
CAPTURES = ROOT / "docs/media/lab-captures"
MEDIA = ROOT / "demos/video-model-flow"
W, H = 1600, 900
INK = "#17352f"
MUTED = "#62756b"
GREEN = "#27694f"
CREAM = "#f3f5ee"
FONT = Path("C:/Windows/Fonts")

CHAPTERS = [
    {
        "id": "overview",
        "title": "One sample. One evidence flow.",
        "role": "THE LAB / WHAT YOU ARE WATCHING",
        "screen": "overview",
        "selector": ".evidence-view",
        "clip": "sample.mp4",
        "bullets": [
            "Real video + recorded model outputs",
            "Voice → SAM → Spark → decision",
            "Wonder → follow-up → batch memory",
        ],
        "takeaway": "An edited walkthrough, not a live inference session.",
        "narration": "Welcome to the model flow lab. This edited walkthrough uses captured lab screens and outputs from real Meta API calls. We follow one tomato through an accelerated video, then connect its visual history to an inspection workflow. The product name is still undecided. No live sensor readings were supplied.",
    },
    {
        "id": "voice",
        "title": "01 / Voice becomes a request",
        "role": "MUSE VOICE TRANSCRIBE",
        "screen": "voice",
        "selector": ".inspector",
        "bullets": [
            "Input: a spoken request",
            "Output: transcript text",
            "The transcript informs the planning task",
        ],
        "takeaway": "Synthetic input speech; real transcription model.",
        "narration": "First, Muse Voice Transcribe turns a spoken request into text. The original tomato video is silent, so this test uses a separately synthesized demonstration request. The real model returned the transcript shown in the lab. That text is included in the history passed to the planner. Here is the demonstration request.",
        "append_request": True,
    },
    {
        "id": "sam",
        "title": "02 / Locate and track the tomato",
        "role": "SAM 3.1 / SEGMENTATION",
        "screen": "sam",
        "selector": ".inspector",
        "clip": "overlay.mp4",
        "bullets": [
            "Input: video + the prompt 'tomato'",
            "Output: object boxes and pixel masks",
            "110 video frames decoded and rendered",
        ],
        "takeaway": "The colored overlay is actual SAM output.",
        "narration": "Next, SAM three point one receives the video and the short prompt, tomato. It returns an object box and a pixel mask for the tomato in each analyzed frame. We decoded masks for all one hundred and ten frames and rendered this overlay movie. SAM supplies the object's location and shape. It does not assign an inspection or food safety verdict.",
    },
    {
        "id": "spark",
        "title": "03 / Explain the visible changes",
        "role": "MUSE SPARK / VIDEO UNDERSTANDING",
        "screen": "spark",
        "selector": ".inspector",
        "bullets": [
            "Input: the full video",
            "Output: 8 structured observations",
            "Earlier: mild; later: severe visual concern",
        ],
        "takeaway": "Playback seconds are not storage hours or days.",
        "narration": "Muse Spark analyzes the full video and returns eight structured checkpoint observations. In this run, it described increasing gray textured coverage near the stem, followed by surface depression and wrinkling. The lab lets you select a checkpoint and read the saved observation with its visibility limits. These are visual categories. The accelerated playback does not reveal the real storage duration.",
    },
    {
        "id": "rescue",
        "title": "04 / Turn evidence into inspection work",
        "role": "RESCUE / APPLICATION POLICY",
        "screen": "rescue",
        "selector": ".inspector",
        "bullets": [
            "Code maps visual categories to points",
            "35 → 70 → 100 in this sample",
            "Sensor: missing / fused score: unavailable",
        ],
        "takeaway": "Priority points are heuristics, not spoilage probabilities.",
        "narration": "Rescue is the decision workflow. Application code maps Spark's visual category to the proposed inspection priority. Here the displayed points increase from thirty five, to seventy, to one hundred as visible concern increases. These are heuristic priority points, not probabilities of spoilage. Because no gas or environmental measurements exist for this video, the sensor channel and combined score remain unavailable.",
    },
    {
        "id": "wonder",
        "title": "05 / Choose the next useful check",
        "role": "MUSE WONDER / INVESTIGATOR",
        "screen": "wonder",
        "selector": ".inspector",
        "bullets": [
            "Calls the allowed history tool",
            "Reads real, saved video observations",
            "Requests missing evidence; cannot run hardware",
        ],
        "takeaway": "The displayed plan uses the full recorded clip.",
        "narration": "Muse Wonder powers the Investigator planning step. It made a real history tool call, received the saved video observations and returned this read only plan. It compared earlier and later evidence, requested additional views and identified the missing sensor protocol. This is a full clip summary. The model did not perform a physical measurement or an A B group test, and it did not approve stock for sale.",
    },
    {
        "id": "history",
        "title": "06 / Remember and follow up",
        "role": "SHELFWATCH / BATCH MEMORY",
        "screen": "history",
        "selector": "#history-list",
        "bullets": [
            "One batch ID links every observation",
            "Keep model outputs and evidence together",
            "Demo tasks are saved only in this browser",
        ],
        "takeaway": "No real stock action is claimed by the demo.",
        "narration": "ShelfWatch keeps the evidence under one batch identity. The timeline connects each checkpoint, mask and observation to the same sample. In the lab you can create a follow up task and mark the demonstration reviewed. Those actions are local to the browser. In the future app, a vendor would confirm an actual inspection or stock outcome, and the next plan would use that saved history.",
    },
    {
        "id": "receipts",
        "title": "Every recommendation has a record",
        "role": "RECEIPTS / LIMITS / NEXT BUILD STEP",
        "screen": "receipts",
        "selector": "#model-cards",
        "bullets": [
            "Inspect response IDs, usage and tool traces",
            "4 real model integrations; one sample",
            "Next: batch storage + real sensor sessions",
        ],
        "takeaway": "Real model integration; physical validation is still ahead.",
        "narration": "Finally, the model receipts show response identifiers, usage and the planning tool trace. This demonstrates all four required model integrations and how their outputs fit together. The next build step is to connect real batch storage, controlled sensor sessions and human confirmed actions. This video is an explanation of the lab, not evidence of food safety or validated shelf life.",
    },
]


def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)


def wrapped(draw, text, xy, width, size=25, fill=INK, bold=False, spacing=9):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=font(size, bold)) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=font(size, bold), fill=fill)
        y += size + spacing
    return y


def crop_capture(chapter):
    path = CAPTURES / (chapter["screen"] + ".png")
    image = Image.open(path).convert("RGB")
    boxes = json.loads(path.with_suffix(".json").read_text())
    box = boxes[chapter["selector"]]
    top, left = max(0, round(box["y"])), max(0, round(box["x"]))
    height = min(round(box["height"]), 700 if chapter["id"] == "history" else 850)
    return image.crop((left, top, left + round(box["width"]), top + height))


def base_frame(chapter, number):
    image = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 9), fill=GREEN)
    draw.text((48, 30), "MODEL FLOW LAB / NARRATED WALKTHROUGH", font=font(15, True), fill=GREEN)
    draw.text((48, 62), chapter["title"], font=font(40, True), fill=INK)
    draw.text((1450, 43), f"{number:02d} / 08", font=font(21), fill=MUTED)
    draw.rounded_rectangle(
        (48, 138, 1068, 716), radius=12, fill="white", outline="#dce3d7", width=2
    )
    if not chapter.get("clip"):
        screenshot = crop_capture(chapter)
        screenshot.thumbnail((990, 548), Image.Resampling.LANCZOS)
        image.paste(
            screenshot, (48 + (1020 - screenshot.width) // 2, 151 + (550 - screenshot.height) // 2)
        )
    y = wrapped(draw, chapter["role"], (1110, 151), 420, 18, GREEN, True)
    y += 28
    for i, bullet in enumerate(chapter["bullets"], 1):
        draw.ellipse((1110, y + 6, 1133, y + 29), fill="#d9e8c4")
        draw.text((1117, y + 6), str(i), font=font(13, True), fill=GREEN)
        y = wrapped(draw, bullet, (1149, y), 385, 25, INK, False, 9) + 30
    draw.rounded_rectangle((1105, max(y, 515), 1550, max(y, 515) + 126), radius=8, fill="#e4ecd9")
    wrapped(draw, chapter["takeaway"], (1122, max(y, 515) + 17), 410, 22, GREEN, True, 8)
    draw.rounded_rectangle((48, 749, 1552, 849), radius=8, fill="#132c29")
    draw.text(
        (50, 869),
        "Video: Lionel Allorge / Wikimedia Commons / CC BY-SA 3.0 | Edited: resized, sampled, overlays + narration",
        font=font(14),
        fill=MUTED,
    )
    return image


def wav_seconds(path):
    with wave.open(str(path)) as wav:
        return wav.getnframes() / wav.getframerate()


def stamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cues(text, duration, start=0):
    words = text.split()
    groups, group = [], []
    for word in words:
        if len(" ".join(group + [word])) > 108 and group:
            groups.append(group)
            group = []
        group.append(word)
        if word.endswith((".", "?", "!")) and len(group) >= 7:
            groups.append(group)
            group = []
    if group:
        groups.append(group)
    result, current = [], start
    for group in groups:
        end = current + duration * len(group) / len(words)
        result.append((current, end, "\n".join(textwrap.wrap(" ".join(group), width=86))))
        current = end
    return result


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (WORK / "audio").mkdir(exist_ok=True)
    (WORK / "chapters.json").write_text(json.dumps(CHAPTERS, indent=2), encoding="utf-8")
    # Synthesize locally. No voice clone or remote generation service is used.
    env = os.environ.copy()
    env["WALKTHROUGH_DIR"] = str(WORK)
    speech = """
$base = $env:WALKTHROUGH_DIR
$chapters = Get-Content -LiteralPath (Join-Path $base 'chapters.json') -Raw | ConvertFrom-Json
foreach ($chapter in $chapters) {
  $voice = New-Object -ComObject SAPI.SpVoice
  $voice.Rate = 0
  $stream = New-Object -ComObject SAPI.SpFileStream
  $stream.Format.Type = 22
  $stream.Open((Join-Path $base ('audio/' + $chapter.id + '_narration.wav')), 3, $false)
  $voice.AudioOutputStream = $stream
  $null = $voice.Speak($chapter.narration)
  $stream.Close()
}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", speech],
        env=env,
        check=True,
        capture_output=True,
    )
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    all_cues, offset, chapter_lines = [], 0.0, []
    transcript = [
        "# Model flow lab - narrated video",
        "",
        "Edited walkthrough of actual recorded model outputs. Narration synthesized locally.",
        "",
        "Source video: [Pourrissement tomate](https://commons.wikimedia.org/wiki/File:Pourrissement_tomate.webm) by Lionel Allorge, Wikimedia Commons. "
        "Selected license: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). "
        "Changes: resizing, frame sampling, model overlays, edited lab captures and explanatory narration. Derived media uses the same license.",
        "",
    ]
    for number, chapter in enumerate(CHAPTERS, 1):
        name = chapter["id"]
        narration = WORK / "audio" / (name + "_narration.wav")
        narration_duration = wav_seconds(narration)
        audio = narration
        local_cues = cues(chapter["narration"], narration_duration)
        if chapter.get("append_request"):
            audio = WORK / "audio" / (name + "_with_request.wav")
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(narration),
                    "-i",
                    str(MEDIA / "voice_request.wav"),
                    "-filter_complex",
                    "[0:a]aresample=24000,aformat=channel_layouts=mono[a];[1:a]aresample=24000,aformat=channel_layouts=mono[b];[a][b]concat=n=2:v=0:a=1[out]",
                    "-map",
                    "[out]",
                    "-c:a",
                    "pcm_s16le",
                    str(audio),
                ],
                check=True,
                capture_output=True,
            )
            request = "DEMO REQUEST: Check this tomato batch. Compare earlier and later observations. Tell me what to inspect next, and ask for a sensor measurement if evidence is missing."
            local_cues.extend(
                cues(request, wav_seconds(audio) - narration_duration, narration_duration)
            )
        duration = wav_seconds(audio) + 0.6
        base_frame(chapter, number).save(WORK / (name + ".png"))
        srt = (
            "\n\n".join(
                f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}"
                for i, (a, b, text) in enumerate(local_cues, 1)
            )
            + "\n"
        )
        (WORK / (name + ".srt")).write_text(srt, encoding="utf-8")
        command = [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-framerate",
            "15",
            "-i",
            str(WORK / (name + ".png")),
            "-i",
            str(audio),
        ]
        subtitle = f"subtitles={name}.srt:force_style='FontName=Segoe UI,FontSize=10,PrimaryColour=&H00FFFFFF,Outline=0,MarginV=20,Alignment=2'"
        if chapter.get("clip"):
            command += ["-stream_loop", "-1", "-i", str(MEDIA / chapter["clip"])]
            filters = f"[2:v]scale=1000:562,setsar=1[clip];[0:v][clip]overlay=58:146:shortest=1[scene];[scene]{subtitle}[out]"
        else:
            filters = f"[0:v]{subtitle}[out]"
        command += [
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-map",
            "1:a",
            "-af",
            "apad=pad_dur=0.6",
            "-t",
            str(duration),
            "-r",
            "15",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-movflags",
            "+faststart",
            str(WORK / (name + ".mp4")),
        ]
        subprocess.run(command, cwd=WORK, check=True, capture_output=True)
        chapter_lines.append(f"{stamp(offset).split(',')[0]}  {chapter['title']}")
        all_cues.extend((a + offset, b + offset, text) for a, b, text in local_cues)
        transcript.extend([f"## {chapter['title']}", "", chapter["narration"], ""])
        offset += math.ceil(duration * 15) / 15
        print(f"Rendered {number}/8: {name} ({duration:.1f}s)", flush=True)
    (WORK / "concat.txt").write_text(
        "\n".join(f"file '{chapter['id']}.mp4'" for chapter in CHAPTERS), encoding="utf-8"
    )
    video = OUT / "model_lab_walkthrough.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(WORK / "concat.txt"),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    (OUT / "model_lab_walkthrough.srt").write_text(
        "\n\n".join(
            f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}" for i, (a, b, text) in enumerate(all_cues, 1)
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "model_lab_walkthrough_chapters.txt").write_text(
        "\n".join(chapter_lines), encoding="utf-8"
    )
    (OUT / "model_lab_walkthrough_transcript.md").write_text(
        "\n".join(transcript), encoding="utf-8"
    )
    print(
        f"Video: {video}\nPlanned duration: {offset:.1f}s\nSize: {video.stat().st_size / 1024**2:.1f} MiB",
        flush=True,
    )


if __name__ == "__main__":
    main()
