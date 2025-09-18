# app/features/auth/models.py
from __future__ import annotations

import uuid

from tortoise import fields, models

from app.features.users.models import User


# ---------- 세션 ----------
class Session(models.Model):
    """
    액세스 세션(JWT jti 기준 추적)
    """

    # 세션 PK(UUID)
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 사용자 FK(User) — 사용자 삭제 시 세션도 함께 삭제(CASCADE)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="sessions", on_delete=fields.CASCADE
    )

    # JWT ID(액세스 토큰 고유 식별자)
    jti = fields.CharField(max_length=36, null=False)

    # 접속 IP(IPv4/IPv6 지원)
    ip_address = fields.CharField(max_length=45, null=True)

    # 클라이언트 User-Agent 문자열
    user_agent = fields.CharField(max_length=255, null=True)

    # 세션 만료 시각(액세스 토큰 만료 기준)
    expires_at = fields.DatetimeField(null=False)

    # 세션 철회(무효화) 시각
    revoked_at = fields.DatetimeField(null=True)

    # 활성 여부(철회 시 False)
    is_active = fields.BooleanField(null=False, default=True)

    # 생성 시각
    created_at = fields.DatetimeField(auto_now_add=True)

    # 수정 시각
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        # 테이블명
        table = "session"
        # jti 유일 제약(중복 방지)
        unique_together = (("jti",),)


# ---------- API Key ----------
class ApiKey(models.Model):
    """
    API 키 보관(해시 저장)
    """

    # API 키 레코드 PK(UUID)
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 소유자 사용자 FK(User) — 사용자 삭제 시 키도 함께 삭제(CASCADE)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="api_keys", on_delete=fields.CASCADE
    )

    # API 키 해시(예: SHA-256) — 유일 제약
    key_hash = fields.CharField(max_length=64, null=False, unique=True)

    # 권한 스코프 목록(JSON 배열)
    scopes: list[str] = fields.JSONField(null=False, default=list)

    # 키 만료 시각(없으면 무기한)
    expires_at = fields.DatetimeField(null=True)

    # 철회 여부(True면 사용 불가)
    is_revoked = fields.BooleanField(null=False, default=False)

    # 마지막 사용 시각(감사/모니터링)
    last_used_at = fields.DatetimeField(null=True)

    # 생성 시각
    created_at = fields.DatetimeField(auto_now_add=True)

    # 수정 시각
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        # 테이블명
        table = "api_keys"
        # 조회 최적화(보조 인덱스가 필요하면 추가)
        indexes = (("user_id", "is_revoked"),)


# ---------- Refresh Token ----------
class RefreshToken(models.Model):
    """
    리프레시 토큰 저장(해시만 저장) + 로테이션/재사용 탐지용
    """

    # PK(UUID)
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 소유자 — 사용자 삭제 시 리프레시 토큰도 함께 삭제(CASCADE)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="refresh_tokens", on_delete=fields.CASCADE
    )

    # 같은 로그인/디바이스 군 식별자 — family 단위 일괄 차단에 사용
    family_id = fields.UUIDField(index=True)

    # 토큰 고유 식별자(JWT jti) — 유일 제약
    jti = fields.CharField(max_length=36, null=False, unique=True)

    # 원본이 아닌 해시(SHA-256 hex 64자) — 유일 제약
    token_hash = fields.CharField(max_length=64, null=False, unique=True)

    # 활성 여부(철회/만료 시 False)
    is_active = fields.BooleanField(null=False, default=True)

    # 만료 시각
    expires_at = fields.DatetimeField(null=False)

    # 철회(무효화) 시각
    revoked_at = fields.DatetimeField(null=True)

    # 마지막 사용 시각(/refresh 성공 시 갱신)
    last_used_at = fields.DatetimeField(null=True)

    # 발급/사용 당시 IP/UA(선택: 감사/탐지)
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=255, null=True)

    # 생성/수정 시각
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        # 테이블명
        table = "refresh_tokens"
        # 조회 최적화 인덱스(활성 토큰 스캔/가족 철회 최적화)
        indexes = (
            ("user_id", "is_active"),
            ("family_id", "is_active"),
        )
