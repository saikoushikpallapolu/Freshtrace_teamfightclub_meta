"""Exercise the running loopback prototype on attributed public photographs."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        required=True,
        help="Required: requests live inference and spends Meta credits",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--samples", nargs="+", default=["mixed_mold", "market_discard", "basket"])
    parser.add_argument("--output", type=Path, default=Path("tmp/prototype_validation.json"))
    args = parser.parse_args()
    if urlparse(args.base_url).hostname not in {"127.0.0.1", "localhost"}:
        parser.error("This validation helper targets a loopback development API only")
    report = {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "batch_id": args.batch_id,
        "assessment": "Integration test; no independent reference masks or item labels",
        "samples": [],
    }
    with httpx.Client(base_url=args.base_url, timeout=60) as client:
        provenance = client.get("/api/samples").json()
        for sample_id in args.samples:
            response = client.post(
                f"/api/samples/{sample_id}/import", json={"batch_id": args.batch_id}
            )
            response.raise_for_status()
            observation = response.json()
            path = f"/api/batches/{args.batch_id}/observations/{observation['observation_id']}"
            response = client.post(path + "/analysis")
            response.raise_for_status()
            deadline = time.monotonic() + 600
            while True:
                response = client.get(path + "/analysis")
                response.raise_for_status()
                state = response.json()
                if state["job"]["status"] in {"complete", "failed"}:
                    break
                if time.monotonic() > deadline:
                    raise TimeoutError("Analysis exceeded validation deadline; job remains saved")
                time.sleep(2)
            row = {
                "sample": next(p for p in provenance if p["sample_id"] == sample_id),
                "observation_id": observation["observation_id"],
                **state,
            }
            if state["job"]["status"] == "complete":
                overlay = client.get(path + "/artifacts/inspection_overlay.jpg")
                overlay.raise_for_status()
                row["overlay_download_bytes"] = len(overlay.content)
                result = state["job"]["result"]
                counts = {
                    name: sum(obj["category"] == name for obj in result["objects"])
                    for name in ["inspect", "no_visible_concern", "unclear"]
                }
                row["category_counts"] = counts
                print(
                    f"{sample_id}: complete; {len(result['objects'])} masks; {counts}", flush=True
                )
            else:
                print(f"{sample_id}: failed; {state['job']['error_code']}", flush=True)
            report["samples"].append(row)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    return 0 if all(r["job"]["status"] == "complete" for r in report["samples"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
