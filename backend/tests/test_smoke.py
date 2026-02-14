from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root_smoke():
    resp = client.get("/")
    # Ensure app responds and not an internal error
    assert resp.status_code < 500
