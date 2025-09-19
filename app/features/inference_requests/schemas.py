# app/features/inference/schemas.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.features.inference_requests.models import RequestStatus


class InferenceIn(BaseModel):
    model: str | None = None  # 없으면 400 (명시 요구)
    input: dict[str, Any]


class InferenceOut(BaseModel):
    request_id: str
    output: dict[str, Any]
    latency_ms: int
    model: dict[str, str]  # {"name": "...", "version": "..."}


class RequestOut(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    username: str
    model_name: str
    model_version: str
    status: RequestStatus
    latency_ms: int | None
    error_code: str | None
    created_at: object


class FeedbackIn(BaseModel):
    request_id: str | None = None
    prediction_id: str | None = None
    rating: int | None = Field(default=None, ge=-1, le=1)
    label: str | None = None
    comment: str | None = None

    def target_missing(self) -> bool:
        return not (self.request_id or self.prediction_id)


class FeedbackOut(BaseModel):
    id: str
    request_id: str | None
    prediction_id: str | None
    rating: int | None
    label: str | None
    comment: str | None
    created_at: object
