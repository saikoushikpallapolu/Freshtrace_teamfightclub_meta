"""Start the loopback prototype; optionally read a Meta key without saving it."""

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ask-key",
        action="store_true",
        help="Read Meta key with a hidden prompt; keep in process memory",
    )
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if args.ask_key:
        os.environ["MODEL_API_KEY"] = getpass("Meta API key (hidden; not saved): ").strip()
    os.chdir(ROOT)
    uvicorn.run(
        "backend.api.product:create_app",
        factory=True,
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )


if __name__ == "__main__":
    main()
