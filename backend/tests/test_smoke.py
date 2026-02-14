from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_smoke():
    resp = client.get("/")
    # Ensure app responds and not an internal error
    assert resp.status_code < 500
