"""Typed visual observations. The model does not compute sensor or safety scores."""

import json

from pydantic import BaseModel, ConfigDict, Field

from backend.meta.client import SPARK_MODEL, image_input


class VisualObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    produce_types: list[str] = Field(min_length=1)
    visible_observations: list[str] = Field(min_length=1)
    visibility_limits: list[str] = Field(min_length=1)


def observe_image(client, data_url: str):
    schema = VisualObservation.model_json_schema()
    response = client.responses.create(
        model=SPARK_MODEL,
        input=image_input(
            "Record only produce types and appearance visible in this image. Include visibility "
            "limits. Do not infer smell, chemicals, food safety or exact remaining life. "
            "Return JSON matching the supplied schema.", data_url),
        text={"format": {"type": "json_schema", "name": "visual_observation",
                         "strict": True, "schema": schema}},
        max_output_tokens=4096,
    )
    if response.status != "completed":
        raise ValueError("Structured vision response did not complete.")
    observation = VisualObservation.model_validate(json.loads(response.output_text))
    return response, observation
