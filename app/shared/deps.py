# 권한/인증 DI 훅
from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: str
    role: str = "user"
    email: str


async def get_current_user() -> CurrentUser:
    # TODO: JWT 파싱/검증 후 유저 로드
    return CurrentUser(
        id="00000000-0000-0000-0000-000000000000",
        role="admin",
        email="admin@example.com",
    )
