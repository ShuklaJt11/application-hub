from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_smoke():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Backend is running"}


def test_cors_preflight_allows_frontend_origin():
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_header_present_on_error_response():
    response = client.post(
        "/api/auth/signup",
        headers={"Origin": "http://localhost:5174"},
        json={},
    )

    assert response.status_code in {422, 500}
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"
