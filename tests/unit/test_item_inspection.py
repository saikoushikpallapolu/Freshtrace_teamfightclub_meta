"""Structured-ID/crop boundaries with synthetic geometry, without API requests."""

import json
from types import SimpleNamespace

import pytest
from PIL import Image

from backend.meta.inspection import InspectionFailure, inspect_photo


def test_mask_picking_uses_foreground_not_overlapping_boxes(tmp_path):
    from PIL import ImageDraw

    from backend.meta.inspection import render_hit_map

    for name, box in [("one.png", (0, 0, 3, 4)), ("two.png", (4, 0, 7, 4))]:
        mask = Image.new("L", (8, 8))
        ImageDraw.Draw(mask).rectangle(box, fill=255)
        mask.save(tmp_path / name)
    render_hit_map([{"mask_file": "one.png"}, {"mask_file": "two.png"}], (8, 8), tmp_path)
    with Image.open(tmp_path / "hit_map.png") as image:
        assert image.getpixel((1, 1))[0] == 1
        assert image.getpixel((6, 1))[0] == 2
        assert image.getpixel((6, 7))[0] == 0


def test_item_crop_alignment_and_unknown_ids_rejected(tmp_path, monkeypatch):
    import backend.meta.inspection as module

    source = tmp_path / "source.jpg"
    Image.new("RGB", (100, 60), "red").save(source)
    monkeypatch.setattr(module, "parse_segmentation", lambda *args: None)

    def geometry(result, image, directory):
        Image.new("L", image.size, 255).save(directory / "mask_000.png")
        return {
            "objects": [
                {
                    "object_id": "provider-7",
                    "bounds": [10, 5, 60, 55],
                    "mask_file": "mask_000.png",
                    "foreground_pixels": 2500,
                }
            ]
        }

    monkeypatch.setattr(module, "render_segmentation", geometry)

    class Provider:
        def __init__(self, object_id):
            self.responses = self
            self.calls = []
            self.object_id = object_id

        def create(self, **kwargs):
            self.calls.append(kwargs)
            output = (
                ""
                if len(self.calls) == 1
                else json.dumps(
                    {
                        "items": [
                            {
                                "object_id": self.object_id,
                                "category": "inspect",
                                "observations": ["marks"],
                                "visibility_limits": ["hidden side"],
                            }
                        ],
                        "scene_limits": ["One view"],
                    }
                )
            )
            return SimpleNamespace(status="completed", output_text=output)

    provider = Provider("T01")
    receipts = []
    result = inspect_photo(provider, source, tmp_path / "good", lambda *args: receipts.append(args))
    assert result["objects"][0]["provider_object_id"] == "provider-7"
    assert result["objects"][0]["object_id"] == "T01"
    assert len(provider.calls) == 2 and len(receipts) == 2
    content = provider.calls[1]["input"][0]["content"]
    assert len([part for part in content if part["type"] == "input_image"]) == 2
    assert (tmp_path / "good/inspection_overlay.jpg").exists()
    with pytest.raises(InspectionFailure, match="visual_object_ids_mismatch"):
        inspect_photo(Provider("wrong"), source, tmp_path / "bad", lambda *args: None)
