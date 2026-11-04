"""Start the visual workspace, sensor API, or AWS telemetry worker."""

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("product", "sensor", "worker"), default="product")
    parser.add_argument(
        "--ask-key",
        action="store_true",
        help="Read Meta key with a hidden prompt; keep in process memory",
    )
    parser.add_argument("--port", type=int, help="Default: product 8080; sensor 8081")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    if args.ask_key:
        os.environ["MODEL_API_KEY"] = getpass("Meta API key (hidden; not saved): ").strip()
    os.chdir(ROOT)
    if args.mode == "worker":
        from backend.inference_service import InferenceEngineService

        InferenceEngineService().run_stream_listener()
        return
    target = (
        "backend.api.product:create_app" if args.mode == "product" else "backend.api.routes:app"
    )
    uvicorn.run(
        target,
        factory=args.mode == "product",
        host="127.0.0.1",
        port=args.port or (8080 if args.mode == "product" else 8081),
        access_log=False,
        log_level=os.getenv("APP_LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
