"""Offline integration-boundary checks; no credential or live provider access."""

import json
from types import SimpleNamespace

import pytest
from meta_sam_parser import CompletedOutcome, image_segmentation_format
from PIL import Image

from backend.meta.client import image_input, load_image, make_client
from backend.meta.planner import plan_with_history
from backend.meta.segmentation import parse_segmentation, render_segmentation
from backend.meta.vision import VisualObservation


def test_image_orientation_matches_uploaded_pixels(tmp_path):
    path = tmp_path / "portrait.jpg"
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (80, 40), "red").save(path, exif=exif)
    image, data_url = load_image(path)
    assert image.size == (40, 80)
    assert data_url.startswith("data:image/jpeg;base64,")


@pytest.mark.parametrize("key", ["", "masked...value", "masked\u2026value", "***"])
def test_reject_masked_key_without_network(key):
    with pytest.raises(ValueError):
        make_client(key)


def test_image_request_shape():
    request = image_input("tomato", "data:image/jpeg;base64,AA")
    assert request[0]["content"][0]["text"] == "tomato"
    assert request[0]["content"][1]["type"] == "input_image"


def test_incomplete_sam_is_not_success():
    with pytest.raises(ValueError, match="incomplete"):
        parse_segmentation("", "incomplete")


def test_malformed_sam_is_not_success():
    with pytest.raises(ValueError, match="diagnostics"):
        parse_segmentation("<0f>0<|box;x1=bad|>", "completed")


def test_empty_sam_matches_not_a_visual_pass(tmp_path):
    result = image_segmentation_format().create_parser().finish(CompletedOutcome()).result
    report = render_segmentation(result, Image.new("RGB", (16, 16)), tmp_path)
    assert report["mask_count"] == 0
    assert not report["nonempty_masks"]


def test_vision_requires_limits_and_forbids_risk_probability():
    with pytest.raises(ValueError):
        VisualObservation(
            produce_types=["tomato"], visible_observations=["red"], visibility_limits=[]
        )
    with pytest.raises(ValueError):
        VisualObservation(
            produce_types=["tomato"],
            visible_observations=["red"],
            visibility_limits=["underside hidden"],
            risk_probability=0.99,
        )


class Item:
    def __init__(self, type_, **values):
        self.type = type_
        self.__dict__.update(values)

    def model_dump(self, **_):
        return self.__dict__.copy()


class FakeClient:
    def __init__(self, arguments, repeat=False):
        self.responses = self
        self.calls = []
        self.arguments = arguments
        self.repeat = repeat

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1 or self.repeat:
            return SimpleNamespace(
                status="completed",
                output_text="",
                output=[
                    Item("reasoning", id="reason-1"),
                    Item(
                        "function_call",
                        name="get_batch_history",
                        arguments=json.dumps(self.arguments),
                        call_id="call-1",
                    ),
                ],
            )
        return SimpleNamespace(
            status="completed",
            output_text="Take a new photo; sensor evidence is missing.",
            output=[],
        )


def test_planner_real_tool_result_round_trip_contract():
    client = FakeClient({"batch_id": "A"})
    responses, trace = plan_with_history(client, "A", {"data_source": "test_fixture"})
    assert len(responses) == 2
    assert all(call["tool_choice"] == "auto" for call in client.calls)
    assert trace[0]["data_source"] == "test_fixture"
    assert any(item.get("type") == "reasoning" for item in client.calls[1]["input"])
    assert any(item.get("type") == "function_call_output" for item in client.calls[1]["input"])


def test_planner_rejects_wrong_batch():
    with pytest.raises(ValueError, match="unauthorized"):
        plan_with_history(FakeClient({"batch_id": "OTHER"}), "A", {})


def test_planner_enforces_round_budget():
    with pytest.raises(ValueError, match="budget"):
        plan_with_history(FakeClient({"batch_id": "A"}, repeat=True), "A", {})
