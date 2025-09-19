# app/features/inference/models.py
from __future__ import annotations

from enum import Enum
from typing import Any
import uuid

from tortoise import fields, models

from app.features.users.models import User


class RequestStatus(str, Enum):
    """추론 요청 처리 상태"""

    pending = "PENDING"
    ok = "OK"
    err = "ERR"


class RequestRecord(models.Model):
    """
    추론 요청 단위 로그
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 요청자
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="inference_requests", on_delete=fields.CASCADE
    )

    # 어떤 모델로 호출했는가 (레지스트리 기준)
    model_name = fields.CharField(max_length=100, null=False)
    model_version = fields.CharField(max_length=50, null=False)

    # 상태/지연/오류 요약
    status: RequestStatus = fields.CharEnumField(
        RequestStatus, default=RequestStatus.pending, null=False
    )
    latency_ms = fields.IntField(null=True)
    error_code = fields.CharField(max_length=50, null=True)

    # 입력 요약/메타(선택)
    input_meta: dict[str, Any] = fields.JSONField(null=False, default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "inference_requests"
        indexes = (("user_id", "created_at"), ("model_name", "created_at"))


class PredictionRecord(models.Model):
    """
    추론 결과(요청:결과 = 1:N 허용; 필요하면 1:1로 사용)
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    request: fields.ForeignKeyRelation[RequestRecord] = fields.ForeignKeyField(
        "models.RequestRecord", related_name="predictions", on_delete=fields.CASCADE
    )

    output: dict[str, Any] = fields.JSONField(null=False, default=dict)
    score: dict[str, Any] = fields.JSONField(null=False, default=dict)  # 점수/확률 등
    meta: dict[str, Any] = fields.JSONField(null=False, default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "predictions"
        indexes = (("request_id",),)


class FeedbackRecord(models.Model):
    """
    피드백(요청 또는 예측에 연결)
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 둘 중 하나만 채워도 됨
    request: fields.ForeignKeyNullableRelation[RequestRecord] = fields.ForeignKeyField(
        "models.RequestRecord", related_name="feedbacks", on_delete=fields.SET_NULL, null=True
    )
    prediction: fields.ForeignKeyNullableRelation[PredictionRecord] = fields.ForeignKeyField(
        "models.PredictionRecord", related_name="feedbacks", on_delete=fields.SET_NULL, null=True
    )

    # 간단 평점(-1~+1) 또는 라벨
    rating = fields.IntField(null=True)  # 유효성은 스키마에서 검사
    label = fields.CharField(max_length=50, null=True)
    comment = fields.TextField(null=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="feedbacks", on_delete=fields.CASCADE
    )

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "feedback"
        indexes = (("request_id",), ("prediction_id",), ("user_id", "created_at"))
