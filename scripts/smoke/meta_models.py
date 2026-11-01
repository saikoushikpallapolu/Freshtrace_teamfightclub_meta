"""Opt-in hosted Meta API checks; no API calls or credential reads on import."""

import argparse
import base64
from datetime import datetime, timezone
from getpass import getpass
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4


BASE_URL = "https://api.meta.ai/v1"
MODELS = {
    "muse": "muse-spark-1.3",
    "vision": "muse-spark-1.3",
    "wonder": "muse-wonder-1.0",
    "sam": "sam-3.1",
}


def image_data_url(path):
    """Accept common image signatures; reject missing/non-image input before billing."""
    raw = path.read_bytes()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError("Use a non-empty JPEG, PNG or WebP image smaller than 10 MiB.")
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif raw.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ValueError("Image must be a JPEG, PNG or WebP file, not a renamed file.")
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def make_input(mode, image=None, object_name="tomato"):
    if mode == "muse":
        return "Reply with exactly: Meta Muse API access works."
    if mode == "wonder":
        return (
            "A produce vendor has one sensor and ten minutes. Batch A has an old photo; "
            "batch B has visible surface damage. Propose a short inspection plan. "
            "Do not invent sensor readings or claim anything is safe to eat."
        )
    prompt = object_name if mode == "sam" else (
        "Describe only what is visible in this produce photo: produce types, apparent "
        "surface damage or discoloration, and visibility limits. Do not infer smell, "
        "chemical measurements, food safety or exact remaining shelf life."
    )
    return [{"role": "user", "content": [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": image},
    ]}]


def save_json(path, data, key):
    # Provider responses normally never contain auth; redact defensively anyway.
    encoded = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(encoded.replace(key, "[REDACTED]"), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODELS, help="Run one real request, not all models.")
    parser.add_argument("--image", type=Path, help="Local JPEG/PNG/WebP; uploaded to Meta.")
    parser.add_argument("--object", default="tomato", help="SAM object phrase, e.g. tomato.")
    args = parser.parse_args(argv)

    try:
        if args.mode in {"vision", "sam"} and args.image is None:
            parser.error("--image is required for vision and sam")
        if args.mode not in {"vision", "sam"} and args.image is not None:
            parser.error("--image is only used by vision and sam")
        if not args.object.strip():
            parser.error("--object must name an object")
        image = image_data_url(args.image) if args.image is not None else None
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    try:
        from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
    except ImportError:
        print("Install the smoke-test dependency: python -m pip install -r "
              "scripts/smoke/requirements.txt", file=sys.stderr)
        return 2

    key = os.environ.get("MODEL_API_KEY", "").strip()
    if not key:
        try:
            key = getpass("Paste the FULL Meta API key (hidden): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo key entered.", file=sys.stderr)
            return 2
    if not key or "..." in key or "\u2026" in key or "*" in key:
        print("Use the complete key, not the masked dashboard preview.", file=sys.stderr)
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    root = Path(__file__).resolve().parents[2]
    out = root / "tmp" / "meta_smoke" / run_id
    out.mkdir(parents=True, exist_ok=False)
    print(f"Calling {MODELS[args.mode]} at Meta. One request; automatic retries disabled.")
    if args.image:
        print("This request sends your selected image to Meta.")
    started = perf_counter()
    try:
        with OpenAI(base_url=BASE_URL, api_key=key, timeout=120.0, max_retries=0) as client:
            request = {"model": MODELS[args.mode],
                       "input": make_input(args.mode, image, args.object.strip())}
            if args.mode == "sam":
                # SAM uses its special-token grammar in the output-text lane.
                with client.responses.stream(**request) as stream:
                    for _event in stream:
                        pass
                    response = stream.get_final_response()
            else:
                response = client.responses.create(**request, max_output_tokens=4096)
    except APIStatusError as exc:
        hints = {
            400: "Check the request/image format and any model-specific requirements.",
            401: "Check that the full key was copied and has not been revoked.",
            402: "Check billing verification and active credits on this key's team.",
            403: "Check team/model permissions and account/billing verification.",
            404: "Check model availability for this account.",
            429: "Check rate limits and quota/credits; do not repeatedly retry.",
        }
        print(f"HTTP {exc.status_code}: {hints.get(exc.status_code, 'Check provider status and retry later.')}", file=sys.stderr)
        # Preserve the provider's error body, without request headers or credentials.
        save_json(out / "error.json", {"http_status": exc.status_code,
                  "request_id": getattr(exc, "request_id", None),
                  "error": exc.body}, key)
        print(f"Error detail saved to {out / 'error.json'}", file=sys.stderr)
        return 1
    except (APIConnectionError, APITimeoutError):
        print("Connection/timeout failure. Check internet, proxy and api.meta.ai access. "
              "No automatic retry was made.", file=sys.stderr)
        return 1
    except Exception as exc:
        # Streaming provider errors must not dump request headers/base64 images.
        print(f"Request did not complete ({type(exc).__name__}). "
              "No successful model result has been verified.", file=sys.stderr)
        return 1

    text = response.output_text or ""
    save_json(out / "response.json", response.model_dump(mode="json"), key)
    (out / "output.txt").write_text(text.replace(key, "[REDACTED]"), encoding="utf-8")
    print(f"Status: {response.status}; elapsed: {perf_counter() - started:.1f}s")
    print(f"Response ID: {response.id}")
    if response.usage:
        print("Usage:", json.dumps(response.usage.model_dump(mode="json")))
    print(f"Saved response and output: {out}")
    if response.status != "completed":
        print("INCOMPLETE: inspect response.json; this is not a passing model check.")
        return 1
    if not text.strip():
        print("No output text. Inspect response.json for refusals or other output.")
        return 1
    if args.mode == "sam":
        print("SAM completed. Encoded segmentation is in output.txt.")
        print("Next: decode/render it with Meta's SAM parser, or inspect the image in "
              "the SAM Playground. Completion alone does not validate mask quality.")
    else:
        print("\n" + text.replace(key, "[REDACTED]"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
