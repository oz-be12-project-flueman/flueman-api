# app/features/inference/repository.py
from __future__ import annotations

from typing import Any

from app.features.inference_requests.models import (
    FeedbackRecord,
    PredictionRecord,
    RequestRecord,
    RequestStatus,
)


class InferenceRepository:
    # ── 요청 생성/완료 ────────────────────────────────────────────
    async def create_request(
        self,
        *,
        user_id: str,
        model_name: str,
        model_version: str,
        input_meta: dict[str, Any],
    ) -> RequestRecord:
        return await RequestRecord.create(
            user_id=user_id,
            model_name=model_name,
            model_version=model_version,
            status=RequestStatus.pending,
            input_meta=input_meta or {},
        )

    async def finish_request_ok(self, *, req_id: str, latency_ms: int) -> None:
        await RequestRecord.filter(id=req_id).update(status=RequestStatus.ok, latency_ms=latency_ms)

    async def finish_request_err(
        self, *, req_id: str, error_code: str, latency_ms: int | None = None
    ) -> None:
        await RequestRecord.filter(id=req_id).update(
            status=RequestStatus.err, error_code=error_code, latency_ms=latency_ms
        )

    # ── 결과/조회 ────────────────────────────────────────────────
    async def create_prediction(
        self,
        *,
        request_id: str,
        output: dict,
        score: dict | None = None,
        meta: dict | None = None,
    ) -> PredictionRecord:
        return await PredictionRecord.create(
            request_id=request_id,
            output=output or {},
            score=score or {},
            meta=meta or {},
        )

    async def get_request(self, req_id: str) -> RequestRecord | None:
        return await RequestRecord.get_or_none(id=req_id)

    async def get_prediction_by_request(self, req_id: str) -> PredictionRecord | None:
        return await PredictionRecord.get_or_none(request_id=req_id)

    # ── 피드백 ───────────────────────────────────────────────────
    async def create_feedback(
        self,
        *,
        user_id: str,
        request_id: str | None,
        prediction_id: str | None,
        rating: int | None,
        label: str | None,
        comment: str | None,
    ) -> FeedbackRecord:
        return await FeedbackRecord.create(
            user_id=user_id,
            request_id=request_id,
            prediction_id=prediction_id,
            rating=rating,
            label=label,
            comment=comment,
        )
