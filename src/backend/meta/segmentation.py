"""Strict SAM result parsing and image-aligned mask rendering, without network I/O."""

from dataclasses import asdict
from pathlib import Path

from meta_sam_parser import CompletedOutcome, decode_mask_to_raster, image_segmentation_format
from PIL import Image, ImageDraw


def parse_segmentation(text: str, status: str):
    if status != "completed":
        raise ValueError("Refusing to parse an incomplete SAM response as a success.")
    parser = image_segmentation_format().create_parser()
    parser.push(text)
    result = parser.finish(CompletedOutcome()).result
    if result.diagnostics:
        raise ValueError("SAM parser diagnostics: " + ", ".join(d.code for d in result.diagnostics))
    return result


def render_segmentation(result, image: Image.Image, output_dir: Path) -> dict:
    """Save per-object masks and a review overlay; empty matches are not a pass."""
    output_dir.mkdir(parents=True, exist_ok=True)
    overlay = image.convert("RGBA")
    colors = [(0, 220, 150), (255, 180, 0), (90, 150, 255), (255, 80, 140)]
    objects = []
    for record in result.records:
        if record.kind != "mask":
            continue
        b = record.bounds
        bounds = tuple(int(v) for v in (b.left, b.top, b.right, b.bottom))
        left, top, right, bottom = bounds
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise ValueError("SAM mask bounds do not match the oriented source image.")
        size = (right - left, bottom - top)
        if size != (record.mask.width, record.mask.height):
            raise ValueError("SAM mask raster size differs from its image bounds.")
        raster = decode_mask_to_raster(record.mask)
        mask = Image.frombytes("L", size, bytes(v * 255 for v in raster))
        pixels = sum(raster)
        if not pixels:
            raise ValueError("SAM returned an empty object mask.")
        # Object IDs are provider strings: use a local sequence for safe filenames.
        filename = f"mask_{len(objects):03d}.png"
        full_mask = Image.new("L", image.size)
        full_mask.paste(mask, (left, top))
        full_mask.save(output_dir / filename)
        color = colors[len(objects) % len(colors)]
        tint = Image.new("RGBA", image.size, (*color, 0))
        tint.putalpha(full_mask.point(lambda v: 90 if v else 0))
        overlay = Image.alpha_composite(overlay, tint)
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((left, top, right - 1, bottom - 1), outline=(*color, 255), width=3)
        draw.text((left + 3, top + 3), f"object {record.object_id}", fill=(255, 255, 255, 255),
                  stroke_width=1, stroke_fill=(0, 0, 0, 255))
        objects.append({"object_id": record.object_id, "bounds": list(bounds),
                        "foreground_pixels": pixels, "mask_file": filename})
    overlay.convert("RGB").save(output_dir / "sam_overlay.jpg", quality=95)
    return {"width": image.width, "height": image.height, "mask_count": len(objects),
            "objects": objects, "diagnostics": [asdict(d) for d in result.diagnostics],
            "nonempty_masks": bool(objects)}
