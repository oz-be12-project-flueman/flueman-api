# app/features/inference/service.py
from __future__ import annotations

from datetime import UTC, datetime
import time
from typing import Any

from fastapi import HTTPException, status

from app.features.inference_requests.models import RequestRecord
from app.features.inference_requests.repository import InferenceRepository
from app.features.inference_requests.schemas import (
    FeedbackIn,
    FeedbackOut,
    InferenceIn,
    InferenceOut,
    RequestOut,
)
from app.features.models_registry.repository import ModelsRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_request_out(r: RequestRecord) -> RequestOut:
    return RequestOut(
        id=str(r.id),
        username=str(r.user.username),
        model_name=r.model_name,
        model_version=r.model_version,
        status=r.status,
        latency_ms=r.latency_ms,
        error_code=r.error_code,
        created_at=r.created_at,
    )


class InferenceService:
    repo_cls = InferenceRepository
    models_repo_cls = ModelsRepository

    def __init__(self) -> None:
        self.repo = self.repo_cls()
        self.models_repo = self.models_repo_cls()

    # ── 추론 실행(동기; 데모/더미 호출) ─────────────────────────────
    async def run_inference(self, *, user_id: str, payload: InferenceIn) -> InferenceOut:
        # 1) 모델 name 필수
        if not payload.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="model name required"
            )

        # 2) 활성 모델 조회
        active = await self.models_repo.get_active_by_name(payload.model)
        if not active:
            raise HTTPException(status_code=404, detail="active model not found for given name")

        # 3) 요청 레코드 생성
        req = await self.repo.create_request(
            user_id=user_id,
            model_name=active.name,
            model_version=active.version,
            input_meta={"keys": list(payload.input.keys())[:10]},  # 간단 요약
        )

        # 4) 모델 호출(더미): 실제로는 외부 모델 서버/함수 호출로 교체
        t0 = time.perf_counter()
        try:
            # ---- 더미 추론 결과 ----
            output: dict[str, Any] = {
                "echo": payload.input,
                "model": {"name": active.name, "version": active.version},
            }
            # -----------------------
            latency_ms = int((time.perf_counter() - t0) * 1000)

            # 5) 결과 저장 & 요청 상태 완료
            _pred = await self.repo.create_prediction(request_id=str(req.id), output=output)
            await self.repo.finish_request_ok(req_id=str(req.id), latency_ms=latency_ms)

            return InferenceOut(
                request_id=str(req.id),
                output=output,
                latency_ms=latency_ms,
                model={"name": active.name, "version": active.version},
            )
        except Exception:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            await self.repo.finish_request_err(
                req_id=str(req.id), error_code="model_error", latency_ms=latency_ms
            )
            raise HTTPException(status_code=502, detail="model inference failed") from None

    # ── 단건 요청 조회 ────────────────────────────────────────────
    async def get_request_detail(self, *, req_id: str) -> RequestOut:
        r = await self.repo.get_request(req_id)
        if not r:
            raise HTTPException(status_code=404, detail="request not found")
        return _to_request_out(r)

    # ── 피드백 저장 ───────────────────────────────────────────────
    async def create_feedback(self, *, user_id: str, payload: FeedbackIn) -> FeedbackOut:
        if payload.target_missing():
            raise HTTPException(status_code=400, detail="request_id or prediction_id is required")
        fb = await self.repo.create_feedback(
            user_id=user_id,
            request_id=payload.request_id,
            prediction_id=payload.prediction_id,
            rating=payload.rating,
            label=payload.label,
            comment=payload.comment,
        )
        return FeedbackOut(
            id=str(fb.id),
            request_id=str(fb.request) if fb.request else None,
            prediction_id=str(fb.prediction) if fb.prediction else None,
            rating=fb.rating,
            label=fb.label,
            comment=fb.comment,
            created_at=fb.created_at,
        )
