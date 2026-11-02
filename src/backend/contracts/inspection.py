"""Visible evidence contracts; inspection categories are not food-safety labels."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["inspect", "no_visible_concern", "unclear"]
PROMPT_VERSION = "tomato-items-v2"


class ItemEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    object_id: str = Field(min_length=1, max_length=30)
    category: Category
    observations: list[str] = Field(min_length=1, max_length=6)
    visibility_limits: list[str] = Field(min_length=1, max_length=4)


class ItemInspection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ItemEvidence] = Field(min_length=1, max_length=32)
    scene_limits: list[str] = Field(min_length=1, max_length=6)


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    object_id: str = Field(min_length=1, max_length=30)
    category: Category
    note: str = Field(min_length=1, max_length=500)
