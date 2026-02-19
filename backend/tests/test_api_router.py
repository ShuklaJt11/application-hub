from fastapi.testclient import TestClient

from app.api.router import api_router
from app.main import app


def test_api_router_contains_auth_endpoints():
    route_paths = {route.path for route in api_router.routes}
    assert "/api/auth/signup" in route_paths
    assert "/api/auth/login" in route_paths


def test_main_app_exposes_auth_endpoints():
    client = TestClient(app)
    route_paths = {route.path for route in client.app.routes}

    assert "/api/auth/signup" in route_paths
    assert "/api/auth/login" in route_paths
