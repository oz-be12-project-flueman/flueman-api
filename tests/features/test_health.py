from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    resp = client.get("/health")
    # 라우터가 200만 주면 일단 통과
    assert resp.status_code == 200
    # 선택: body 구조가 있다면 키 체크
    # assert resp.json().get("status") == "ok"
