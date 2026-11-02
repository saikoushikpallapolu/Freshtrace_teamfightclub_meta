"""Bounded image validation and immutable local originals/derived JPEGs."""

import hashlib
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000
TYPES = {"JPEG": "image/jpeg", "PNG": "image/png"}


class InvalidImage(ValueError):
    pass


@dataclass(frozen=True)
class StoredImage:
    sha256: str
    original_key: str
    normalized_key: str
    content_type: str
    byte_size: int
    width: int
    height: int


class LocalMediaStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def resolve(self, key):
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Media key escapes storage root")
        return path

    def store(self, data: bytes, content_type: str) -> StoredImage:
        if not data or len(data) > MAX_BYTES:
            raise InvalidImage("Image must contain 1 byte to 10 MiB")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as image:
                    actual = TYPES.get(image.format)
                    if actual is None or actual != content_type:
                        raise InvalidImage("Content-Type must match a JPEG or PNG image")
                    if (
                        image.width * image.height > MAX_PIXELS
                        or getattr(image, "n_frames", 1) != 1
                    ):
                        raise InvalidImage("Use one still image of at most 20 megapixels")
                    image.verify()
                with Image.open(BytesIO(data)) as image:
                    normalized = ImageOps.exif_transpose(image).convert("RGB")
                    normalized.load()
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise InvalidImage("Image cannot be safely decoded") from exc
        digest = hashlib.sha256(data).hexdigest()
        original_key = f"{digest[:2]}/{digest}/original"
        normalized_key = f"{digest[:2]}/{digest}/normalized-v1.jpg"
        output = BytesIO()
        normalized.save(output, format="JPEG", quality=95)
        self._write_once(original_key, data)
        self._write_once(normalized_key, output.getvalue())
        return StoredImage(
            digest,
            original_key,
            normalized_key,
            actual,
            len(data),
            normalized.width,
            normalized.height,
        )

    def _write_once(self, key, data):
        """Publish a complete file atomically; concurrent same-hash uploads are safe."""
        import os
        import tempfile

        path = self.resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # Hard-link publication cannot overwrite an existing immutable object.
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass
        finally:
            Path(temporary).unlink(missing_ok=True)
