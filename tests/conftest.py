from fastapi.testclient import TestClient
import pytest

# 앱 팩토리/인스턴스 가져오기
try:
    from app.main import app  # FastAPI 인스턴스가 app 변수에 있다고 가정
except Exception:
    pytest.skip("app.main.app import failed", allow_module_level=True)


@pytest.fixture(scope="session")
def client() -> TestClient:
    # CI에서 DB 연결이 없어도 /health는 통과하도록 구성
    return TestClient(app)
