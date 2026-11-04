"""Explicit live validation of text, typed vision, SAM masks and read-only planning."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def write_json(path, value, key):
    text = json.dumps(value, indent=2, ensure_ascii=False)
    path.write_text(text.replace(key, "[REDACTED]"), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        required=True,
        help="Required acknowledgment: makes real billed requests to Meta.",
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["text", "vision", "sam", "planner"],
        default=["text", "vision", "sam", "planner"],
    )
    parser.add_argument(
        "--image", type=Path, default=ROOT / "frontend/src/assets/fresh_vegetables_bg.jpg"
    )
    parser.add_argument("--object", default="tomato")
    args = parser.parse_args(argv)
    from backend.meta.client import SAM_MODEL, SPARK_MODEL, image_input, load_image, make_client
    from backend.meta.planner import plan_with_history
    from backend.meta.segmentation import parse_segmentation, render_segmentation
    from backend.meta.vision import observe_image

    checks = list(dict.fromkeys(args.checks))
    image = data_url = None
    if "vision" in checks or "sam" in checks:
        image, data_url = load_image(args.image)
    key = (
        os.environ.get("MODEL_API_KEY", "").strip()
        or getpass("Full Meta API key (hidden): ").strip()
    )
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    directory = ROOT / "tmp/meta_validation" / run
    directory.mkdir(parents=True)
    if image:
        image.save(directory / "input.jpg", quality=95)
    summary = {
        "run_id": run,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": "https://api.meta.ai/v1",
        "checks": {},
        "image_role": "existing repository image; integration test, not a vendor trial",
        "source_image_sha256": hashlib.sha256(args.image.read_bytes()).hexdigest()
        if image
        else None,
    }
    with make_client(key) as client:
        for check in checks:
            started = perf_counter()
            item = {"passed": False}
            summary["checks"][check] = item
            try:
                if check == "text":
                    response = client.responses.create(
                        model=SPARK_MODEL,
                        input="Reply with exactly: Meta Muse API access works.",
                        max_output_tokens=4096,
                    )
                    responses = [response]
                    if (
                        response.status != "completed"
                        or response.output_text.strip() != "Meta Muse API access works."
                    ):
                        raise ValueError(
                            "Text access check did not return the expected completed answer."
                        )
                    item["text"] = response.output_text
                elif check == "vision":
                    response, observation = observe_image(client, data_url)
                    responses = [response]
                    item["observation"] = observation.model_dump(mode="json")
                elif check == "sam":
                    with client.responses.stream(
                        model=SAM_MODEL,
                        input=image_input(args.object, data_url),
                        metadata={"mask_encoding": "one_bit"},
                    ) as stream:
                        for _event in stream:
                            pass
                        response = stream.get_final_response()
                    responses = [response]
                    result = parse_segmentation(response.output_text, response.status)
                    item["segmentation"] = render_segmentation(result, image, directory / "sam")
                    if not item["segmentation"]["nonempty_masks"]:
                        raise ValueError(
                            "API completed but no nonempty masks matched the test prompt."
                        )
                else:
                    # Explicit synthetic input verifies tools without pretending to query a real batch DB.
                    fixture = json.loads(
                        (ROOT / "data/fixtures/meta_planning_batch.json").read_text()
                    )
                    responses, trace = plan_with_history(client, fixture["batch_id"], fixture)
                    item["tool_trace"] = trace
                    item["plan"] = responses[-1].output_text
                item["passed"] = True
                item["calls"] = [
                    {
                        "model": r.model,
                        "response_id": r.id,
                        "status": r.status,
                        "usage": r.usage.model_dump(mode="json") if r.usage else None,
                    }
                    for r in responses
                ]
                for i, response in enumerate(responses):
                    write_json(
                        directory / f"{check}_response_{i}.json",
                        response.model_dump(mode="json"),
                        key,
                    )
            except Exception as exc:
                # Do not serialize the exception or request; headers can contain credentials.
                item["error_type"] = type(exc).__name__
                item["http_status"] = getattr(exc, "status_code", None)
                if isinstance(exc, ValueError):
                    item["detail"] = str(exc).replace(key, "[REDACTED]")
                elif getattr(exc, "body", None) is not None:
                    item["provider_error"] = exc.body
            item["elapsed_seconds"] = round(perf_counter() - started, 2)
            write_json(directory / "summary.json", summary, key)
            print(
                f"{check}: {'PASS' if item['passed'] else 'FAIL'} ({item['elapsed_seconds']}s)",
                flush=True,
            )
    print(f"Results: {directory}")
    return 0 if all(item["passed"] for item in summary["checks"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
