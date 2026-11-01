"""Small server-only Meta Responses client with explicit credentials and limits."""

import base64
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageOps

BASE_URL = "https://api.meta.ai/v1"
SPARK_MODEL = "muse-spark-1.3"
WONDER_MODEL = "muse-wonder-1.0"
SAM_MODEL = "sam-3.1"


def load_image(path: Path) -> tuple[Image.Image, str]:
    """Normalize orientation; send the exact same pixels that overlays will use."""
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Use an image smaller than 10 MiB.")
    with Image.open(path) as source:
        if source.width * source.height > 20_000_000:
            raise ValueError("Use an image smaller than 20 megapixels.")
        image = ImageOps.exif_transpose(source).convert("RGB")
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return image, "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def image_input(prompt: str, data_url: str) -> list:
    return [{"role": "user", "content": [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": data_url},
    ]}]


def make_client(key: str) -> OpenAI:
    if not key.strip() or any(marker in key for marker in ("...", "\u2026", "*")):
        raise ValueError("Use a full unmasked Meta API key.")
    return OpenAI(base_url=BASE_URL, api_key=key.strip(), timeout=120.0, max_retries=0)
