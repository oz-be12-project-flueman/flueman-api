# app/features/inference/router.py
from __future__ import annotations

from fastapi import APIRouter

from app.features.inference_requests.schemas import (
    FeedbackIn,
    FeedbackOut,
    InferenceIn,
    InferenceOut,
    RequestOut,
)
from app.features.inference_requests.service import InferenceService
from app.shared.auth import AdminOrSelfByUserId, CurrentUser

router = APIRouter(prefix="/inference", tags=["inference"])

ReqIdPath = str  # 가독성용 별칭


@router.post("", response_model=InferenceOut)
async def run_inference(payload: InferenceIn, current: CurrentUser) -> InferenceOut:
    """
    활성 모델(name)로 동기 추론 수행 + 요청/결과 저장
    """
    svc = InferenceService()
    return await svc.run_inference(user_id=str(current.id), payload=payload)


@router.get("/requests/{request_id}", response_model=RequestOut)
async def get_request(request_id: ReqIdPath, _: AdminOrSelfByUserId) -> RequestOut:
    """
    추론 요청 단건 조회(본인 또는 admin)
    """
    svc = InferenceService()
    out = await svc.get_request_detail(req_id=request_id)

    return out


@router.post("/feedback", response_model=FeedbackOut)
async def create_feedback(payload: FeedbackIn, current: CurrentUser) -> FeedbackOut:
    """
    요청/예측에 대한 피드백 저장
    """
    svc = InferenceService()
    return await svc.create_feedback(user_id=str(current.id), payload=payload)
